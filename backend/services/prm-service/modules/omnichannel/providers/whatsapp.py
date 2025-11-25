"""
WhatsApp Business API Provider
Supports Meta WhatsApp Cloud API and Twilio WhatsApp
"""
import hmac
import hashlib
import json
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


class WhatsAppProvider(BaseChannelProvider):
    """
    WhatsApp Business API provider.
    Supports both Meta Cloud API and Twilio WhatsApp.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_version = config.get('api_version', 'v18.0')
        self.phone_number_id = config.get('whatsapp_phone_number_id')
        self.business_account_id = config.get('whatsapp_business_account_id')
        self.access_token = config.get('credentials', {}).get('access_token')
        self.webhook_verify_token = config.get('credentials', {}).get('webhook_verify_token')
        self.app_secret = config.get('credentials', {}).get('app_secret')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.session: Optional[aiohttp.ClientSession] = None

        # Twilio WhatsApp alternative
        self.use_twilio = config.get('provider_type') == 'twilio_whatsapp'
        if self.use_twilio:
            self.twilio_account_sid = config.get('credentials', {}).get('account_sid')
            self.twilio_auth_token = config.get('credentials', {}).get('auth_token')
            self.twilio_from_number = config.get('from_phone_number')

    async def initialize(self) -> bool:
        """Initialize WhatsApp provider"""
        try:
            self.session = aiohttp.ClientSession()

            if self.use_twilio:
                # Verify Twilio credentials
                # Implementation would check Twilio API
                pass
            else:
                # Verify Meta API access
                if not self.phone_number_id or not self.access_token:
                    raise ProviderError("Missing WhatsApp API credentials")

                # Test API access
                url = f"{self.base_url}/{self.phone_number_id}"
                headers = {"Authorization": f"Bearer {self.access_token}"}

                async with self.session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise ProviderError(
                            f"WhatsApp API error: {error_data.get('error', {}).get('message')}"
                        )

            self.is_initialized = True
            logger.info(f"WhatsApp provider initialized: {self.phone_number_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp provider: {e}")
            self.health_status = ProviderStatus.UNHEALTHY
            return False

    async def send_message(self, payload: MessagePayload) -> ProviderResult:
        """Send WhatsApp message"""
        if not self.is_initialized:
            await self.initialize()

        try:
            recipient = self.format_phone_number(payload.recipient)

            if self.use_twilio:
                return await self._send_via_twilio(recipient, payload)
            else:
                return await self._send_via_meta(recipient, payload)

        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            raise ProviderError(
                str(e),
                error_code="SEND_FAILED",
                is_retriable=True,
                original_error=e
            )

    async def _send_via_meta(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Send via Meta WhatsApp Cloud API"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Build message payload
        message_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient
        }

        # Determine message type
        if payload.buttons:
            message_data["type"] = "interactive"
            message_data["interactive"] = self._build_interactive_message(payload)
        elif payload.attachments:
            attachment = payload.attachments[0]
            media_type = attachment.get('type', 'document')
            message_data["type"] = media_type
            message_data[media_type] = {
                "link": attachment.get('url'),
                "caption": payload.content
            }
            if media_type == "document":
                message_data[media_type]["filename"] = attachment.get('filename')
        else:
            message_data["type"] = "text"
            message_data["text"] = {
                "preview_url": True,
                "body": payload.content
            }

        # Add reply context if present
        if payload.reply_to:
            message_data["context"] = {"message_id": payload.reply_to}

        async with self.session.post(url, json=message_data, headers=headers) as response:
            result = await response.json()

            if response.status == 200:
                message_id = result.get('messages', [{}])[0].get('id')
                return ProviderResult(
                    success=True,
                    external_id=message_id,
                    status="sent",
                    metadata={"provider_response": result}
                )
            else:
                error = result.get('error', {})
                error_code = str(error.get('code', 'UNKNOWN'))
                error_message = error.get('message', 'Unknown error')

                # Determine if retriable
                retriable_codes = ['131047', '131048', '131053']  # Rate limits, temporary failures
                is_retriable = error_code in retriable_codes

                return ProviderResult(
                    success=False,
                    error_code=error_code,
                    error_message=error_message,
                    is_retriable=is_retriable,
                    metadata={"provider_response": result}
                )

    async def _send_via_twilio(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Send via Twilio WhatsApp"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)

        data = {
            "From": f"whatsapp:{self.twilio_from_number}",
            "To": f"whatsapp:{recipient}",
            "Body": payload.content
        }

        # Add media if present
        if payload.attachments:
            data["MediaUrl"] = payload.attachments[0].get('url')

        async with self.session.post(url, data=data, auth=auth) as response:
            result = await response.json()

            if response.status in [200, 201]:
                return ProviderResult(
                    success=True,
                    external_id=result.get('sid'),
                    status="sent",
                    cost=float(result.get('price', 0)) if result.get('price') else None,
                    metadata={"provider_response": result}
                )
            else:
                return ProviderResult(
                    success=False,
                    error_code=str(result.get('code', 'UNKNOWN')),
                    error_message=result.get('message', 'Unknown error'),
                    is_retriable=result.get('code') in [20003, 20429],  # Auth, rate limit
                    metadata={"provider_response": result}
                )

    def _build_interactive_message(self, payload: MessagePayload) -> Dict[str, Any]:
        """Build interactive message payload"""
        buttons = payload.buttons[:3]  # Max 3 buttons

        if len(buttons) <= 3:
            # Reply buttons
            return {
                "type": "button",
                "body": {"text": payload.content},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn.get('id', f"btn_{i}"),
                                "title": btn.get('text', btn.get('title', ''))[:20]
                            }
                        }
                        for i, btn in enumerate(buttons)
                    ]
                }
            }
        else:
            # List message for more options
            return {
                "type": "list",
                "body": {"text": payload.content},
                "action": {
                    "button": "Options",
                    "sections": [
                        {
                            "title": "Select",
                            "rows": [
                                {
                                    "id": btn.get('id', f"btn_{i}"),
                                    "title": btn.get('text', btn.get('title', ''))[:24],
                                    "description": btn.get('description', '')[:72]
                                }
                                for i, btn in enumerate(payload.buttons[:10])
                            ]
                        }
                    ]
                }
            }

    async def send_template(
        self,
        recipient: str,
        template_name: str,
        variables: Dict[str, Any],
        language: str = "en"
    ) -> ProviderResult:
        """Send template message"""
        if not self.is_initialized:
            await self.initialize()

        recipient = self.format_phone_number(recipient)

        if self.use_twilio:
            # Twilio uses ContentSid for templates
            return await self._send_twilio_template(recipient, template_name, variables)

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Build template components
        components = []
        if variables:
            body_params = [
                {"type": "text", "text": str(v)}
                for v in variables.values()
            ]
            if body_params:
                components.append({
                    "type": "body",
                    "parameters": body_params
                })

        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components
            }
        }

        async with self.session.post(url, json=message_data, headers=headers) as response:
            result = await response.json()

            if response.status == 200:
                message_id = result.get('messages', [{}])[0].get('id')
                return ProviderResult(
                    success=True,
                    external_id=message_id,
                    status="sent",
                    metadata={"provider_response": result}
                )
            else:
                error = result.get('error', {})
                return ProviderResult(
                    success=False,
                    error_code=str(error.get('code', 'UNKNOWN')),
                    error_message=error.get('message', 'Unknown error'),
                    is_retriable=False,
                    metadata={"provider_response": result}
                )

    async def _send_twilio_template(
        self,
        recipient: str,
        template_name: str,
        variables: Dict[str, Any]
    ) -> ProviderResult:
        """Send Twilio content template"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)

        data = {
            "From": f"whatsapp:{self.twilio_from_number}",
            "To": f"whatsapp:{recipient}",
            "ContentSid": template_name,
            "ContentVariables": json.dumps(variables)
        }

        async with self.session.post(url, data=data, auth=auth) as response:
            result = await response.json()

            return ProviderResult(
                success=response.status in [200, 201],
                external_id=result.get('sid'),
                status="sent" if response.status in [200, 201] else "failed",
                error_code=str(result.get('code')) if result.get('code') else None,
                error_message=result.get('message'),
                metadata={"provider_response": result}
            )

    async def parse_webhook(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse WhatsApp webhook payload"""
        webhook = WebhookPayload(raw_data=data)

        try:
            if self.use_twilio:
                return self._parse_twilio_webhook(data)

            # Meta Cloud API webhook
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})

                    # Handle incoming messages
                    for message in value.get('messages', []):
                        webhook.message_id = message.get('id')
                        webhook.sender = message.get('from')
                        webhook.timestamp = datetime.fromtimestamp(int(message.get('timestamp', 0)))

                        msg_type = message.get('type')
                        if msg_type == 'text':
                            webhook.content = message.get('text', {}).get('body')
                            webhook.content_type = 'text'
                        elif msg_type == 'image':
                            webhook.content_type = 'image'
                            webhook.attachments = [message.get('image', {})]
                        elif msg_type == 'document':
                            webhook.content_type = 'document'
                            webhook.attachments = [message.get('document', {})]
                        elif msg_type == 'audio':
                            webhook.content_type = 'audio'
                            webhook.attachments = [message.get('audio', {})]
                        elif msg_type == 'video':
                            webhook.content_type = 'video'
                            webhook.attachments = [message.get('video', {})]
                        elif msg_type == 'location':
                            webhook.content_type = 'location'
                            webhook.content = json.dumps(message.get('location', {}))
                        elif msg_type == 'interactive':
                            webhook.content_type = 'interactive'
                            interactive = message.get('interactive', {})
                            if interactive.get('type') == 'button_reply':
                                webhook.content = interactive.get('button_reply', {}).get('id')
                            elif interactive.get('type') == 'list_reply':
                                webhook.content = interactive.get('list_reply', {}).get('id')
                        elif msg_type == 'button':
                            webhook.content_type = 'button'
                            webhook.content = message.get('button', {}).get('payload')

                    # Handle status updates
                    for status in value.get('statuses', []):
                        webhook.message_id = status.get('id')
                        webhook.status = status.get('status')
                        webhook.timestamp = datetime.fromtimestamp(int(status.get('timestamp', 0)))
                        webhook.recipient = status.get('recipient_id')

                        if status.get('errors'):
                            error = status['errors'][0]
                            webhook.error_code = str(error.get('code'))
                            webhook.error_message = error.get('message')

        except Exception as e:
            logger.error(f"Failed to parse WhatsApp webhook: {e}")

        return webhook

    def _parse_twilio_webhook(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse Twilio WhatsApp webhook"""
        webhook = WebhookPayload(raw_data=data)

        webhook.message_id = data.get('MessageSid') or data.get('SmsSid')
        webhook.sender = data.get('From', '').replace('whatsapp:', '')
        webhook.recipient = data.get('To', '').replace('whatsapp:', '')
        webhook.content = data.get('Body')
        webhook.status = data.get('MessageStatus') or data.get('SmsStatus')

        if data.get('ErrorCode'):
            webhook.error_code = data.get('ErrorCode')
            webhook.error_message = data.get('ErrorMessage')

        # Handle media
        num_media = int(data.get('NumMedia', 0))
        for i in range(num_media):
            webhook.attachments.append({
                'url': data.get(f'MediaUrl{i}'),
                'content_type': data.get(f'MediaContentType{i}')
            })

        return webhook

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """Verify webhook signature"""
        if self.use_twilio:
            # Twilio signature verification would be implemented here
            return True

        if not self.app_secret:
            logger.warning("No app_secret configured, skipping webhook verification")
            return True

        expected_signature = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    async def health_check(self) -> ProviderStatus:
        """Check WhatsApp API health"""
        try:
            if not self.session:
                await self.initialize()

            if self.use_twilio:
                # Check Twilio status
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}.json"
                auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)

                async with self.session.get(url, auth=auth) as response:
                    if response.status == 200:
                        self.health_status = ProviderStatus.HEALTHY
                    else:
                        self.health_status = ProviderStatus.UNHEALTHY
            else:
                # Check Meta API
                url = f"{self.base_url}/{self.phone_number_id}"
                headers = {"Authorization": f"Bearer {self.access_token}"}

                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        self.health_status = ProviderStatus.HEALTHY
                    else:
                        self.health_status = ProviderStatus.UNHEALTHY

        except Exception as e:
            logger.error(f"WhatsApp health check failed: {e}")
            self.health_status = ProviderStatus.UNHEALTHY

        self.last_health_check = datetime.utcnow()
        return self.health_status

    def validate_recipient(self, recipient: str) -> bool:
        """Validate WhatsApp number format"""
        cleaned = ''.join(c for c in recipient if c.isdigit())
        return len(cleaned) >= 10 and len(cleaned) <= 15

    def get_message_cost(self, payload: MessagePayload) -> float:
        """Estimate WhatsApp message cost"""
        # WhatsApp Business pricing varies by region and message type
        # These are approximate USD costs
        if payload.template_id:
            # Template messages (business-initiated)
            return 0.05
        else:
            # Session messages (within 24-hour window)
            return 0.03

    async def close(self):
        """Close provider session"""
        if self.session:
            await self.session.close()
            self.session = None
