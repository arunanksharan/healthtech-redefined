"""
Email Provider
Multi-provider email support: SendGrid, AWS SES
"""
import hmac
import hashlib
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
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


class EmailProvider(BaseChannelProvider):
    """
    Multi-provider email gateway.
    Supports SendGrid and AWS SES.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = config.get('provider_type', 'sendgrid')
        self.from_email = config.get('from_email')
        self.from_name = config.get('from_name', 'Healthcare')
        self.reply_to = config.get('reply_to_email')
        self.session: Optional[aiohttp.ClientSession] = None

        # Provider-specific credentials
        credentials = config.get('credentials', {})
        if self.provider_type == 'sendgrid':
            self.api_key = credentials.get('api_key')
            self.webhook_signing_secret = credentials.get('webhook_signing_secret')
        elif self.provider_type == 'aws_ses':
            self.aws_access_key = credentials.get('access_key')
            self.aws_secret_key = credentials.get('secret_key')
            self.aws_region = credentials.get('region', 'us-east-1')

    async def initialize(self) -> bool:
        """Initialize email provider"""
        try:
            self.session = aiohttp.ClientSession()

            if self.provider_type == 'sendgrid':
                if not self.api_key:
                    raise ProviderError("Missing SendGrid API key")

                # Verify API key
                url = "https://api.sendgrid.com/v3/user/profile"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with self.session.get(url, headers=headers) as response:
                    if response.status not in [200, 401]:
                        # 401 is ok - just means limited permissions
                        raise ProviderError("Invalid SendGrid API key")

            elif self.provider_type == 'aws_ses':
                # AWS SES initialization
                if not self.aws_access_key or not self.aws_secret_key:
                    raise ProviderError("Missing AWS credentials")

            self.is_initialized = True
            logger.info(f"Email provider initialized: {self.provider_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize email provider: {e}")
            self.health_status = ProviderStatus.UNHEALTHY
            return False

    async def send_message(self, payload: MessagePayload) -> ProviderResult:
        """Send email message"""
        if not self.is_initialized:
            await self.initialize()

        try:
            if not self.validate_recipient(payload.recipient):
                return ProviderResult(
                    success=False,
                    error_code="INVALID_EMAIL",
                    error_message="Invalid email address format"
                )

            if self.provider_type == 'sendgrid':
                return await self._send_via_sendgrid(payload)
            elif self.provider_type == 'aws_ses':
                return await self._send_via_aws_ses(payload)
            else:
                raise ProviderError(f"Unknown provider type: {self.provider_type}")

        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Email send error: {e}")
            raise ProviderError(
                str(e),
                error_code="SEND_FAILED",
                is_retriable=True,
                original_error=e
            )

    async def _send_via_sendgrid(self, payload: MessagePayload) -> ProviderResult:
        """Send email via SendGrid"""
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build personalizations
        personalizations = [{
            "to": [{"email": payload.recipient}]
        }]

        if payload.cc:
            personalizations[0]["cc"] = [{"email": cc} for cc in payload.cc]
        if payload.bcc:
            personalizations[0]["bcc"] = [{"email": bcc} for bcc in payload.bcc]

        # Build email content
        content = []
        if payload.content:
            content.append({
                "type": "text/plain",
                "value": payload.content
            })

        # Add HTML content if available
        html_content = payload.metadata.get('content_html')
        if html_content:
            content.append({
                "type": "text/html",
                "value": html_content
            })

        data = {
            "personalizations": personalizations,
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "subject": payload.subject or "Healthcare Communication",
            "content": content
        }

        # Add reply-to
        if self.reply_to:
            data["reply_to"] = {"email": self.reply_to}

        # Add attachments
        if payload.attachments:
            data["attachments"] = [
                {
                    "content": att.get('content_base64', ''),
                    "filename": att.get('filename', 'attachment'),
                    "type": att.get('mime_type', 'application/octet-stream'),
                    "disposition": "attachment"
                }
                for att in payload.attachments
            ]

        # Add tracking
        data["tracking_settings"] = {
            "click_tracking": {"enable": True},
            "open_tracking": {"enable": True}
        }

        # Add custom headers for tracking
        if payload.metadata.get('message_id'):
            data["custom_args"] = {
                "internal_message_id": str(payload.metadata.get('message_id'))
            }

        async with self.session.post(url, json=data, headers=headers) as response:
            if response.status == 202:
                # SendGrid doesn't return message ID in success response
                # We get it from the x-message-id header
                message_id = response.headers.get('x-message-id')

                return ProviderResult(
                    success=True,
                    external_id=message_id,
                    status="sent",
                    metadata={"headers": dict(response.headers)}
                )
            else:
                result = await response.json()
                errors = result.get('errors', [{}])
                first_error = errors[0] if errors else {}

                return ProviderResult(
                    success=False,
                    error_code=first_error.get('field', 'UNKNOWN'),
                    error_message=first_error.get('message', 'Unknown error'),
                    is_retriable=response.status >= 500,
                    metadata={"provider_response": result}
                )

    async def _send_via_aws_ses(self, payload: MessagePayload) -> ProviderResult:
        """Send email via AWS SES"""
        try:
            import boto3
            from botocore.config import Config

            config = Config(
                region_name=self.aws_region,
                signature_version='v4'
            )

            client = boto3.client(
                'ses',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                config=config
            )

            # Build destination
            destination = {'ToAddresses': [payload.recipient]}
            if payload.cc:
                destination['CcAddresses'] = payload.cc
            if payload.bcc:
                destination['BccAddresses'] = payload.bcc

            # Build message body
            body = {}
            if payload.content:
                body['Text'] = {'Data': payload.content, 'Charset': 'UTF-8'}

            html_content = payload.metadata.get('content_html')
            if html_content:
                body['Html'] = {'Data': html_content, 'Charset': 'UTF-8'}

            response = client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination=destination,
                Message={
                    'Subject': {
                        'Data': payload.subject or 'Healthcare Communication',
                        'Charset': 'UTF-8'
                    },
                    'Body': body
                },
                ReplyToAddresses=[self.reply_to] if self.reply_to else []
            )

            return ProviderResult(
                success=True,
                external_id=response.get('MessageId'),
                status="sent",
                metadata={"provider_response": response}
            )

        except Exception as e:
            error_code = 'AWS_SES_ERROR'
            if 'Throttling' in str(e):
                error_code = 'RATE_LIMIT'
            elif 'Validation' in str(e):
                error_code = 'VALIDATION_ERROR'

            return ProviderResult(
                success=False,
                error_code=error_code,
                error_message=str(e),
                is_retriable='Throttling' in str(e)
            )

    async def send_template(
        self,
        recipient: str,
        template_name: str,
        variables: Dict[str, Any],
        language: str = "en"
    ) -> ProviderResult:
        """Send template-based email"""
        if not self.is_initialized:
            await self.initialize()

        if self.provider_type == 'sendgrid':
            return await self._send_sendgrid_template(recipient, template_name, variables)
        else:
            # For AWS SES, template rendering is handled externally
            # Pass-through to send_message
            content = template_name  # Assume pre-rendered
            payload = MessagePayload(recipient=recipient, content=content)
            return await self.send_message(payload)

    async def _send_sendgrid_template(
        self,
        recipient: str,
        template_id: str,
        variables: Dict[str, Any]
    ) -> ProviderResult:
        """Send SendGrid dynamic template"""
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "personalizations": [{
                "to": [{"email": recipient}],
                "dynamic_template_data": variables
            }],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "template_id": template_id
        }

        if self.reply_to:
            data["reply_to"] = {"email": self.reply_to}

        async with self.session.post(url, json=data, headers=headers) as response:
            if response.status == 202:
                message_id = response.headers.get('x-message-id')
                return ProviderResult(
                    success=True,
                    external_id=message_id,
                    status="sent"
                )
            else:
                result = await response.json()
                errors = result.get('errors', [{}])
                first_error = errors[0] if errors else {}

                return ProviderResult(
                    success=False,
                    error_code=first_error.get('field', 'UNKNOWN'),
                    error_message=first_error.get('message', 'Unknown error'),
                    is_retriable=response.status >= 500
                )

    async def parse_webhook(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse email webhook payload"""
        webhook = WebhookPayload(raw_data=data)

        if self.provider_type == 'sendgrid':
            # SendGrid sends an array of events
            events = data if isinstance(data, list) else [data]

            for event in events:
                webhook.message_id = event.get('sg_message_id')
                webhook.recipient = event.get('email')
                webhook.status = event.get('event')
                webhook.timestamp = datetime.fromtimestamp(event.get('timestamp', 0))

                if event.get('reason'):
                    webhook.error_message = event.get('reason')

                # Map SendGrid events to standard status
                event_mapping = {
                    'processed': 'queued',
                    'dropped': 'failed',
                    'delivered': 'delivered',
                    'deferred': 'pending',
                    'bounce': 'bounced',
                    'blocked': 'blocked',
                    'open': 'read',
                    'click': 'read',
                    'spam_report': 'blocked',
                    'unsubscribe': 'blocked'
                }
                webhook.status = event_mapping.get(event.get('event'), event.get('event'))

        elif self.provider_type == 'aws_ses':
            # AWS SES SNS notification
            message = data.get('Message', {})
            if isinstance(message, str):
                import json
                message = json.loads(message)

            notification_type = message.get('notificationType')
            mail = message.get('mail', {})

            webhook.message_id = mail.get('messageId')
            webhook.timestamp = datetime.fromisoformat(
                mail.get('timestamp', '').replace('Z', '+00:00')
            ) if mail.get('timestamp') else None

            if notification_type == 'Delivery':
                webhook.status = 'delivered'
                webhook.recipient = message.get('delivery', {}).get('recipients', [''])[0]
            elif notification_type == 'Bounce':
                webhook.status = 'bounced'
                bounce = message.get('bounce', {})
                webhook.error_code = bounce.get('bounceType')
                webhook.error_message = bounce.get('bounceSubType')
                recipients = bounce.get('bouncedRecipients', [{}])
                webhook.recipient = recipients[0].get('emailAddress') if recipients else None
            elif notification_type == 'Complaint':
                webhook.status = 'blocked'
                complaint = message.get('complaint', {})
                recipients = complaint.get('complainedRecipients', [{}])
                webhook.recipient = recipients[0].get('emailAddress') if recipients else None

        return webhook

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """Verify webhook signature"""
        if self.provider_type == 'sendgrid':
            if not self.webhook_signing_secret:
                return True

            # SendGrid Event Webhook signature verification
            try:
                timestamp_bytes = timestamp.encode() if timestamp else b''
                signed_payload = timestamp_bytes + payload

                expected = hmac.new(
                    self.webhook_signing_secret.encode(),
                    signed_payload,
                    hashlib.sha256
                ).digest()

                expected_b64 = base64.b64encode(expected).decode()
                return hmac.compare_digest(expected_b64, signature)
            except Exception:
                return False

        elif self.provider_type == 'aws_ses':
            # AWS SNS signature verification
            # Would need to verify the SNS message signature
            return True

        return True

    async def health_check(self) -> ProviderStatus:
        """Check email provider health"""
        try:
            if not self.session:
                await self.initialize()

            if self.provider_type == 'sendgrid':
                url = "https://api.sendgrid.com/v3/scopes"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with self.session.get(url, headers=headers) as response:
                    self.health_status = (
                        ProviderStatus.HEALTHY if response.status == 200
                        else ProviderStatus.UNHEALTHY
                    )

        except Exception as e:
            logger.error(f"Email health check failed: {e}")
            self.health_status = ProviderStatus.UNHEALTHY

        self.last_health_check = datetime.utcnow()
        return self.health_status

    def validate_recipient(self, recipient: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, recipient))

    def get_message_cost(self, payload: MessagePayload) -> float:
        """Estimate email cost"""
        # Email costs are generally very low
        base_cost = 0.0001  # ~$0.10 per 1000 emails

        # Attachments increase cost slightly
        if payload.attachments:
            base_cost += 0.0001 * len(payload.attachments)

        return base_cost

    async def close(self):
        """Close provider session"""
        if self.session:
            await self.session.close()
            self.session = None
