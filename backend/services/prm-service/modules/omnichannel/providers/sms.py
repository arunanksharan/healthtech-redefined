"""
SMS Gateway Provider
Multi-provider SMS support: Twilio, AWS SNS, MessageBird, Vonage
"""
import hmac
import hashlib
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from loguru import logger

from .base import (
    BaseChannelProvider,
    MessagePayload,
    WebhookPayload,
    ProviderResult,
    ProviderError,
    ProviderStatus
)


class SMSProvider(BaseChannelProvider):
    """
    Multi-provider SMS gateway.
    Supports Twilio, AWS SNS, MessageBird, and Vonage.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = config.get('provider_type', 'twilio_sms')
        self.from_number = config.get('from_phone_number')
        self.messaging_service_sid = config.get('credentials', {}).get('messaging_service_sid')
        self.session: Optional[aiohttp.ClientSession] = None

        # Provider-specific credentials
        credentials = config.get('credentials', {})
        if self.provider_type == 'twilio_sms':
            self.account_sid = credentials.get('account_sid')
            self.auth_token = credentials.get('auth_token')
        elif self.provider_type == 'aws_sns':
            self.aws_access_key = credentials.get('access_key')
            self.aws_secret_key = credentials.get('secret_key')
            self.aws_region = credentials.get('region', 'us-east-1')
        elif self.provider_type == 'messagebird':
            self.api_key = credentials.get('api_key')
        elif self.provider_type == 'vonage':
            self.api_key = credentials.get('api_key')
            self.api_secret = credentials.get('api_secret')

    async def initialize(self) -> bool:
        """Initialize SMS provider"""
        try:
            self.session = aiohttp.ClientSession()

            if self.provider_type == 'twilio_sms':
                if not self.account_sid or not self.auth_token:
                    raise ProviderError("Missing Twilio credentials")

                # Verify account
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)

                async with self.session.get(url, auth=auth) as response:
                    if response.status != 200:
                        raise ProviderError("Invalid Twilio credentials")

            elif self.provider_type == 'messagebird':
                if not self.api_key:
                    raise ProviderError("Missing MessageBird API key")

                url = "https://rest.messagebird.com/balance"
                headers = {"Authorization": f"AccessKey {self.api_key}"}

                async with self.session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise ProviderError("Invalid MessageBird credentials")

            self.is_initialized = True
            logger.info(f"SMS provider initialized: {self.provider_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize SMS provider: {e}")
            self.health_status = ProviderStatus.UNHEALTHY
            return False

    async def send_message(self, payload: MessagePayload) -> ProviderResult:
        """Send SMS message"""
        if not self.is_initialized:
            await self.initialize()

        try:
            recipient = self.format_phone_number(payload.recipient)

            if not self.validate_recipient(recipient):
                return ProviderResult(
                    success=False,
                    error_code="INVALID_NUMBER",
                    error_message="Invalid phone number format"
                )

            if self.provider_type == 'twilio_sms':
                return await self._send_via_twilio(recipient, payload)
            elif self.provider_type == 'aws_sns':
                return await self._send_via_aws_sns(recipient, payload)
            elif self.provider_type == 'messagebird':
                return await self._send_via_messagebird(recipient, payload)
            elif self.provider_type == 'vonage':
                return await self._send_via_vonage(recipient, payload)
            else:
                raise ProviderError(f"Unknown provider type: {self.provider_type}")

        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            raise ProviderError(
                str(e),
                error_code="SEND_FAILED",
                is_retriable=True,
                original_error=e
            )

    async def _send_via_twilio(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Send SMS via Twilio"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)

        data = {
            "To": recipient,
            "Body": payload.content
        }

        # Use messaging service or from number
        if self.messaging_service_sid:
            data["MessagingServiceSid"] = self.messaging_service_sid
        else:
            data["From"] = self.from_number

        # Add media for MMS
        if payload.attachments:
            data["MediaUrl"] = payload.attachments[0].get('url')

        async with self.session.post(url, data=data, auth=auth) as response:
            result = await response.json()

            if response.status in [200, 201]:
                segments = result.get('num_segments', 1)
                cost = float(result.get('price', 0)) if result.get('price') else None

                return ProviderResult(
                    success=True,
                    external_id=result.get('sid'),
                    status=result.get('status', 'sent'),
                    cost=cost,
                    segments=int(segments) if segments else 1,
                    metadata={"provider_response": result}
                )
            else:
                error_code = str(result.get('code', 'UNKNOWN'))
                is_retriable = error_code in ['20003', '20429', '30001']

                return ProviderResult(
                    success=False,
                    error_code=error_code,
                    error_message=result.get('message', 'Unknown error'),
                    is_retriable=is_retriable,
                    metadata={"provider_response": result}
                )

    async def _send_via_aws_sns(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Send SMS via AWS SNS"""
        try:
            import boto3
            from botocore.config import Config

            config = Config(
                region_name=self.aws_region,
                signature_version='v4'
            )

            client = boto3.client(
                'sns',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                config=config
            )

            response = client.publish(
                PhoneNumber=recipient,
                Message=payload.content,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': self.config.get('sender_id', 'Healthcare')
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )

            return ProviderResult(
                success=True,
                external_id=response.get('MessageId'),
                status="sent",
                metadata={"provider_response": response}
            )

        except Exception as e:
            return ProviderResult(
                success=False,
                error_code="AWS_SNS_ERROR",
                error_message=str(e),
                is_retriable=True
            )

    async def _send_via_messagebird(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Send SMS via MessageBird"""
        url = "https://rest.messagebird.com/messages"
        headers = {
            "Authorization": f"AccessKey {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "originator": self.from_number,
            "recipients": [recipient],
            "body": payload.content
        }

        async with self.session.post(url, json=data, headers=headers) as response:
            result = await response.json()

            if response.status in [200, 201]:
                return ProviderResult(
                    success=True,
                    external_id=result.get('id'),
                    status="sent",
                    metadata={"provider_response": result}
                )
            else:
                return ProviderResult(
                    success=False,
                    error_code=str(result.get('errors', [{}])[0].get('code', 'UNKNOWN')),
                    error_message=result.get('errors', [{}])[0].get('description', 'Unknown error'),
                    is_retriable=response.status >= 500,
                    metadata={"provider_response": result}
                )

    async def _send_via_vonage(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Send SMS via Vonage (Nexmo)"""
        url = "https://rest.nexmo.com/sms/json"

        data = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "from": self.from_number,
            "to": recipient.replace('+', ''),
            "text": payload.content
        }

        async with self.session.post(url, data=data) as response:
            result = await response.json()

            messages = result.get('messages', [{}])
            first_message = messages[0] if messages else {}

            if first_message.get('status') == '0':
                return ProviderResult(
                    success=True,
                    external_id=first_message.get('message-id'),
                    status="sent",
                    cost=float(first_message.get('message-price', 0)),
                    metadata={"provider_response": result}
                )
            else:
                return ProviderResult(
                    success=False,
                    error_code=first_message.get('status', 'UNKNOWN'),
                    error_message=first_message.get('error-text', 'Unknown error'),
                    is_retriable=first_message.get('status') in ['1', '4', '5'],
                    metadata={"provider_response": result}
                )

    async def send_template(
        self,
        recipient: str,
        template_name: str,
        variables: Dict[str, Any],
        language: str = "en"
    ) -> ProviderResult:
        """Send template-based SMS"""
        # SMS doesn't have pre-approved templates like WhatsApp
        # Template rendering is handled by the service layer
        # This is a pass-through to send_message
        content = template_name  # Assume pre-rendered
        payload = MessagePayload(recipient=recipient, content=content)
        return await self.send_message(payload)

    async def parse_webhook(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse SMS webhook payload"""
        webhook = WebhookPayload(raw_data=data)

        if self.provider_type == 'twilio_sms':
            webhook.message_id = data.get('MessageSid') or data.get('SmsSid')
            webhook.sender = data.get('From')
            webhook.recipient = data.get('To')
            webhook.content = data.get('Body')
            webhook.status = data.get('MessageStatus') or data.get('SmsStatus')

            if data.get('ErrorCode'):
                webhook.error_code = data.get('ErrorCode')
                webhook.error_message = data.get('ErrorMessage')

            # Handle inbound media (MMS)
            num_media = int(data.get('NumMedia', 0))
            for i in range(num_media):
                webhook.attachments.append({
                    'url': data.get(f'MediaUrl{i}'),
                    'content_type': data.get(f'MediaContentType{i}')
                })

        elif self.provider_type == 'messagebird':
            webhook.message_id = data.get('id')
            webhook.sender = data.get('originator')
            webhook.recipient = data.get('recipient')
            webhook.content = data.get('body')
            webhook.status = data.get('status')

        elif self.provider_type == 'vonage':
            webhook.message_id = data.get('messageId')
            webhook.sender = data.get('msisdn')
            webhook.recipient = data.get('to')
            webhook.content = data.get('text')
            webhook.status = data.get('status')

            if data.get('err-code'):
                webhook.error_code = data.get('err-code')

        return webhook

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """Verify webhook signature"""
        if self.provider_type == 'twilio_sms':
            # Twilio validates via request URL + auth token
            # Full validation requires URL which is handled in router
            return True

        elif self.provider_type == 'messagebird':
            if not signature:
                return True  # MessageBird signature is optional

            # MessageBird signature verification
            expected = hmac.new(
                self.api_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)

        return True

    async def health_check(self) -> ProviderStatus:
        """Check SMS provider health"""
        try:
            if not self.session:
                await self.initialize()

            if self.provider_type == 'twilio_sms':
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)

                async with self.session.get(url, auth=auth) as response:
                    self.health_status = (
                        ProviderStatus.HEALTHY if response.status == 200
                        else ProviderStatus.UNHEALTHY
                    )

            elif self.provider_type == 'messagebird':
                url = "https://rest.messagebird.com/balance"
                headers = {"Authorization": f"AccessKey {self.api_key}"}

                async with self.session.get(url, headers=headers) as response:
                    self.health_status = (
                        ProviderStatus.HEALTHY if response.status == 200
                        else ProviderStatus.UNHEALTHY
                    )

        except Exception as e:
            logger.error(f"SMS health check failed: {e}")
            self.health_status = ProviderStatus.UNHEALTHY

        self.last_health_check = datetime.utcnow()
        return self.health_status

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format"""
        cleaned = ''.join(c for c in recipient if c.isdigit() or c == '+')
        # Must have country code and be reasonable length
        if cleaned.startswith('+'):
            return len(cleaned) >= 10 and len(cleaned) <= 16
        return False

    def get_message_cost(self, payload: MessagePayload) -> float:
        """Estimate SMS cost"""
        segments = self.get_segments_count(payload.content)

        # Approximate costs per segment by provider
        cost_per_segment = {
            'twilio_sms': 0.0079,
            'aws_sns': 0.0075,
            'messagebird': 0.0065,
            'vonage': 0.0070
        }

        base_cost = cost_per_segment.get(self.provider_type, 0.0079)

        # MMS is more expensive
        if payload.attachments:
            base_cost = 0.02

        return base_cost * segments

    async def close(self):
        """Close provider session"""
        if self.session:
            await self.session.close()
            self.session = None
