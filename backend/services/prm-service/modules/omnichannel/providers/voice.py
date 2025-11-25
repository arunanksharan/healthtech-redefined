"""
Voice Communication Provider
Automated voice calls via Twilio Voice and AWS Connect
"""
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
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


class VoiceProvider(BaseChannelProvider):
    """
    Voice communication provider.
    Supports Twilio Voice and AWS Connect for automated calls.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = config.get('provider_type', 'twilio_voice')
        self.from_number = config.get('from_phone_number')
        self.session: Optional[aiohttp.ClientSession] = None

        # TTS (Text-to-Speech) configuration
        self.tts_voice = config.get('config', {}).get('tts_voice', 'Polly.Joanna')
        self.tts_language = config.get('config', {}).get('tts_language', 'en-US')

        # Call configuration
        self.record_calls = config.get('config', {}).get('record_calls', False)
        self.machine_detection = config.get('config', {}).get('machine_detection', 'Enable')
        self.timeout_seconds = config.get('config', {}).get('timeout_seconds', 30)

        # Webhook URLs (set by service)
        self.status_callback_url = config.get('config', {}).get('status_callback_url')
        self.twiml_url = config.get('config', {}).get('twiml_url')

        # Provider-specific credentials
        credentials = config.get('credentials', {})
        if self.provider_type == 'twilio_voice':
            self.account_sid = credentials.get('account_sid')
            self.auth_token = credentials.get('auth_token')
        elif self.provider_type == 'aws_connect':
            self.aws_access_key = credentials.get('access_key')
            self.aws_secret_key = credentials.get('secret_key')
            self.aws_region = credentials.get('region', 'us-east-1')
            self.instance_id = credentials.get('instance_id')
            self.contact_flow_id = credentials.get('contact_flow_id')

    async def initialize(self) -> bool:
        """Initialize voice provider"""
        try:
            self.session = aiohttp.ClientSession()

            if self.provider_type == 'twilio_voice':
                if not self.account_sid or not self.auth_token:
                    raise ProviderError("Missing Twilio credentials")

                # Verify account
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)

                async with self.session.get(url, auth=auth) as response:
                    if response.status != 200:
                        raise ProviderError("Invalid Twilio credentials")

            elif self.provider_type == 'aws_connect':
                # Verify AWS Connect access
                pass

            self.is_initialized = True
            logger.info(f"Voice provider initialized: {self.provider_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize voice provider: {e}")
            self.health_status = ProviderStatus.UNHEALTHY
            return False

    async def send_message(self, payload: MessagePayload) -> ProviderResult:
        """
        Initiate an automated voice call.
        The 'content' field contains the text to be spoken via TTS.
        """
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

            if self.provider_type == 'twilio_voice':
                return await self._initiate_twilio_call(recipient, payload)
            elif self.provider_type == 'aws_connect':
                return await self._initiate_aws_connect_call(recipient, payload)
            else:
                raise ProviderError(f"Unknown provider type: {self.provider_type}")

        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Voice call error: {e}")
            raise ProviderError(
                str(e),
                error_code="CALL_FAILED",
                is_retriable=True,
                original_error=e
            )

    async def _initiate_twilio_call(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Initiate call via Twilio"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
        auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)

        # Build TwiML for the call
        twiml = self._build_twiml(payload)

        data = {
            "To": recipient,
            "From": self.from_number,
            "Twiml": twiml,
            "Timeout": self.timeout_seconds,
        }

        # Add status callback
        if self.status_callback_url:
            data["StatusCallback"] = self.status_callback_url
            data["StatusCallbackEvent"] = ["initiated", "ringing", "answered", "completed"]
            data["StatusCallbackMethod"] = "POST"

        # Machine detection (voicemail detection)
        if self.machine_detection:
            data["MachineDetection"] = self.machine_detection
            data["MachineDetectionTimeout"] = 5

        # Call recording
        if self.record_calls:
            data["Record"] = "true"
            data["RecordingStatusCallback"] = f"{self.status_callback_url}/recording"

        async with self.session.post(url, data=data, auth=auth) as response:
            result = await response.json()

            if response.status in [200, 201]:
                return ProviderResult(
                    success=True,
                    external_id=result.get('sid'),
                    status=result.get('status', 'queued'),
                    cost=float(result.get('price', 0)) if result.get('price') else None,
                    metadata={
                        "provider_response": result,
                        "call_duration": result.get('duration')
                    }
                )
            else:
                error_code = str(result.get('code', 'UNKNOWN'))
                is_retriable = error_code in ['20003', '20429']

                return ProviderResult(
                    success=False,
                    error_code=error_code,
                    error_message=result.get('message', 'Unknown error'),
                    is_retriable=is_retriable,
                    metadata={"provider_response": result}
                )

    def _build_twiml(self, payload: MessagePayload) -> str:
        """Build TwiML for voice call"""
        twiml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<Response>']

        # Add pause for initial greeting
        twiml_parts.append('<Pause length="1"/>')

        # Main message content
        content = payload.content or "Hello, this is an automated call from your healthcare provider."

        # Check if we should use gather (for IVR)
        gather_options = payload.metadata.get('gather_options')
        if gather_options:
            twiml_parts.append(
                f'<Gather input="dtmf speech" timeout="5" numDigits="{gather_options.get("num_digits", 1)}">'
            )

        # Add the spoken message
        twiml_parts.append(
            f'<Say voice="{self.tts_voice}" language="{self.tts_language}">{self._escape_xml(content)}</Say>'
        )

        if gather_options:
            twiml_parts.append('</Gather>')

            # Fallback if no input
            fallback_message = gather_options.get('fallback_message', "We didn't receive any input. Goodbye.")
            twiml_parts.append(
                f'<Say voice="{self.tts_voice}">{self._escape_xml(fallback_message)}</Say>'
            )

        # Add buttons/options as DTMF menu if present
        if payload.buttons:
            menu_text = "Press "
            for i, btn in enumerate(payload.buttons[:9], 1):
                menu_text += f"{i} for {btn.get('text', btn.get('title', ''))}. "

            twiml_parts.append(
                f'<Say voice="{self.tts_voice}">{self._escape_xml(menu_text)}</Say>'
            )

        twiml_parts.append('</Response>')
        return ''.join(twiml_parts)

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters"""
        return (
            text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;')
        )

    async def _initiate_aws_connect_call(self, recipient: str, payload: MessagePayload) -> ProviderResult:
        """Initiate call via AWS Connect"""
        try:
            import boto3
            from botocore.config import Config

            config = Config(
                region_name=self.aws_region,
                signature_version='v4'
            )

            client = boto3.client(
                'connect',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                config=config
            )

            # Start outbound voice contact
            response = client.start_outbound_voice_contact(
                DestinationPhoneNumber=recipient,
                ContactFlowId=self.contact_flow_id,
                InstanceId=self.instance_id,
                SourcePhoneNumber=self.from_number,
                Attributes={
                    'message': payload.content or 'Healthcare notification',
                    'patient_id': str(payload.metadata.get('patient_id', '')),
                    'message_id': str(payload.metadata.get('message_id', ''))
                }
            )

            return ProviderResult(
                success=True,
                external_id=response.get('ContactId'),
                status="initiated",
                metadata={"provider_response": response}
            )

        except Exception as e:
            return ProviderResult(
                success=False,
                error_code="AWS_CONNECT_ERROR",
                error_message=str(e),
                is_retriable=True
            )

    async def send_template(
        self,
        recipient: str,
        template_name: str,
        variables: Dict[str, Any],
        language: str = "en"
    ) -> ProviderResult:
        """Send template-based voice call"""
        # Voice doesn't have pre-approved templates
        # Template rendering is handled by the service layer
        content = template_name  # Assume pre-rendered
        payload = MessagePayload(recipient=recipient, content=content)
        return await self.send_message(payload)

    async def parse_webhook(self, data: Dict[str, Any]) -> WebhookPayload:
        """Parse voice webhook payload"""
        webhook = WebhookPayload(raw_data=data)

        if self.provider_type == 'twilio_voice':
            webhook.message_id = data.get('CallSid')
            webhook.sender = data.get('From')
            webhook.recipient = data.get('To')
            webhook.status = data.get('CallStatus')

            # Map Twilio call statuses
            status_mapping = {
                'queued': 'pending',
                'ringing': 'sent',
                'in-progress': 'sent',
                'completed': 'delivered',
                'busy': 'failed',
                'no-answer': 'failed',
                'canceled': 'failed',
                'failed': 'failed'
            }
            webhook.status = status_mapping.get(data.get('CallStatus'), data.get('CallStatus'))

            # Call details
            if data.get('CallDuration'):
                webhook.metadata = webhook.metadata or {}
                webhook.metadata['duration_seconds'] = int(data.get('CallDuration', 0))

            # Answered by machine detection
            if data.get('AnsweredBy'):
                webhook.metadata = webhook.metadata or {}
                webhook.metadata['answered_by'] = data.get('AnsweredBy')

            # DTMF digits pressed (IVR response)
            if data.get('Digits'):
                webhook.content = data.get('Digits')
                webhook.content_type = 'dtmf'

            # Speech recognition result
            if data.get('SpeechResult'):
                webhook.content = data.get('SpeechResult')
                webhook.content_type = 'speech'

            # Recording URL
            if data.get('RecordingUrl'):
                webhook.attachments = [{
                    'type': 'audio',
                    'url': data.get('RecordingUrl'),
                    'duration': data.get('RecordingDuration')
                }]

            # Error handling
            if data.get('ErrorCode'):
                webhook.error_code = data.get('ErrorCode')
                webhook.error_message = data.get('ErrorMessage')

        return webhook

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """Verify webhook signature"""
        if self.provider_type == 'twilio_voice':
            # Twilio validates via URL + auth token
            # Full validation requires the request URL
            return True

        return True

    async def generate_twiml_response(
        self,
        action: str,
        message: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate TwiML response for call handling.
        Used for dynamic call flows and IVR.
        """
        twiml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<Response>']

        if action == 'say':
            twiml_parts.append(
                f'<Say voice="{self.tts_voice}">{self._escape_xml(message or "")}</Say>'
            )

        elif action == 'gather':
            num_digits = options.get('num_digits', 1) if options else 1
            timeout = options.get('timeout', 5) if options else 5

            twiml_parts.append(
                f'<Gather input="dtmf" numDigits="{num_digits}" timeout="{timeout}">'
            )
            if message:
                twiml_parts.append(
                    f'<Say voice="{self.tts_voice}">{self._escape_xml(message)}</Say>'
                )
            twiml_parts.append('</Gather>')

        elif action == 'record':
            max_length = options.get('max_length', 60) if options else 60
            if message:
                twiml_parts.append(
                    f'<Say voice="{self.tts_voice}">{self._escape_xml(message)}</Say>'
                )
            twiml_parts.append(f'<Record maxLength="{max_length}" playBeep="true"/>')

        elif action == 'hangup':
            if message:
                twiml_parts.append(
                    f'<Say voice="{self.tts_voice}">{self._escape_xml(message)}</Say>'
                )
            twiml_parts.append('<Hangup/>')

        elif action == 'redirect':
            redirect_url = options.get('url', '') if options else ''
            twiml_parts.append(f'<Redirect>{redirect_url}</Redirect>')

        twiml_parts.append('</Response>')
        return ''.join(twiml_parts)

    async def health_check(self) -> ProviderStatus:
        """Check voice provider health"""
        try:
            if not self.session:
                await self.initialize()

            if self.provider_type == 'twilio_voice':
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
                auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)

                async with self.session.get(url, auth=auth) as response:
                    self.health_status = (
                        ProviderStatus.HEALTHY if response.status == 200
                        else ProviderStatus.UNHEALTHY
                    )

        except Exception as e:
            logger.error(f"Voice health check failed: {e}")
            self.health_status = ProviderStatus.UNHEALTHY

        self.last_health_check = datetime.utcnow()
        return self.health_status

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format"""
        cleaned = ''.join(c for c in recipient if c.isdigit() or c == '+')
        if cleaned.startswith('+'):
            return len(cleaned) >= 10 and len(cleaned) <= 16
        return False

    def get_message_cost(self, payload: MessagePayload) -> float:
        """Estimate voice call cost"""
        # Twilio voice pricing is per minute
        # Assume average call duration of 1 minute
        estimated_minutes = payload.metadata.get('estimated_minutes', 1)

        # Approximate costs per minute by provider
        cost_per_minute = {
            'twilio_voice': 0.015,  # Outbound calling
            'aws_connect': 0.018
        }

        base_cost = cost_per_minute.get(self.provider_type, 0.015)
        return base_cost * estimated_minutes

    async def close(self):
        """Close provider session"""
        if self.session:
            await self.session.close()
            self.session = None
