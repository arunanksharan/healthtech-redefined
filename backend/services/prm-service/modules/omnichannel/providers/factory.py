"""
Provider Factory
Factory pattern for creating and managing channel providers
"""
from typing import Dict, Any, Optional, Type
from uuid import UUID
from loguru import logger

from .base import BaseChannelProvider, ProviderStatus
from .whatsapp import WhatsAppProvider
from .sms import SMSProvider
from .email import EmailProvider
from .voice import VoiceProvider


# Provider type to class mapping
PROVIDER_CLASSES: Dict[str, Type[BaseChannelProvider]] = {
    # WhatsApp
    'meta_whatsapp': WhatsAppProvider,
    'twilio_whatsapp': WhatsAppProvider,

    # SMS
    'twilio_sms': SMSProvider,
    'aws_sns': SMSProvider,
    'messagebird': SMSProvider,
    'vonage': SMSProvider,

    # Email
    'sendgrid': EmailProvider,
    'aws_ses': EmailProvider,

    # Voice
    'twilio_voice': VoiceProvider,
    'aws_connect': VoiceProvider,

    # Push Notifications (placeholder)
    'firebase_push': None,  # To be implemented
}

# Channel to provider type mapping
CHANNEL_DEFAULT_PROVIDERS: Dict[str, str] = {
    'whatsapp': 'meta_whatsapp',
    'sms': 'twilio_sms',
    'email': 'sendgrid',
    'voice': 'twilio_voice',
    'push_notification': 'firebase_push',
}


class ProviderFactory:
    """
    Factory for creating and managing communication providers.
    Implements singleton pattern for provider instances.
    """

    _instances: Dict[str, BaseChannelProvider] = {}
    _configs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_provider(
        cls,
        provider_type: str,
        config: Dict[str, Any]
    ) -> Optional[BaseChannelProvider]:
        """
        Create a new provider instance.

        Args:
            provider_type: Type of provider (e.g., 'twilio_sms', 'sendgrid')
            config: Provider configuration including credentials

        Returns:
            Provider instance or None if not supported
        """
        provider_class = PROVIDER_CLASSES.get(provider_type)

        if not provider_class:
            logger.warning(f"Unknown provider type: {provider_type}")
            return None

        try:
            # Add provider_type to config
            config['provider_type'] = provider_type

            provider = provider_class(config)
            logger.info(f"Created provider: {provider_type}")
            return provider

        except Exception as e:
            logger.error(f"Failed to create provider {provider_type}: {e}")
            return None

    @classmethod
    def get_or_create(
        cls,
        provider_id: UUID,
        provider_type: str,
        config: Dict[str, Any]
    ) -> Optional[BaseChannelProvider]:
        """
        Get existing provider instance or create new one.
        Uses provider_id as cache key for singleton behavior.

        Args:
            provider_id: Unique provider identifier
            provider_type: Type of provider
            config: Provider configuration

        Returns:
            Provider instance
        """
        cache_key = str(provider_id)

        # Check if instance exists and config hasn't changed
        if cache_key in cls._instances:
            existing_config = cls._configs.get(cache_key, {})

            # Simple config comparison (credentials excluded)
            if (existing_config.get('provider_type') == provider_type and
                existing_config.get('from_phone_number') == config.get('from_phone_number') and
                existing_config.get('from_email') == config.get('from_email')):
                return cls._instances[cache_key]

            # Config changed, close old instance
            try:
                old_instance = cls._instances[cache_key]
                if hasattr(old_instance, 'close'):
                    import asyncio
                    asyncio.create_task(old_instance.close())
            except Exception:
                pass

        # Create new instance
        config['provider_id'] = provider_id
        provider = cls.create_provider(provider_type, config)

        if provider:
            cls._instances[cache_key] = provider
            cls._configs[cache_key] = config

        return provider

    @classmethod
    def get_provider(cls, provider_id: UUID) -> Optional[BaseChannelProvider]:
        """
        Get cached provider instance by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            Cached provider instance or None
        """
        return cls._instances.get(str(provider_id))

    @classmethod
    async def initialize_provider(
        cls,
        provider: BaseChannelProvider
    ) -> bool:
        """
        Initialize a provider and cache result.

        Args:
            provider: Provider instance to initialize

        Returns:
            True if initialization successful
        """
        try:
            return await provider.initialize()
        except Exception as e:
            logger.error(f"Provider initialization failed: {e}")
            return False

    @classmethod
    async def health_check_all(cls) -> Dict[str, ProviderStatus]:
        """
        Run health checks on all cached providers.

        Returns:
            Dict of provider_id -> health status
        """
        results = {}

        for provider_id, provider in cls._instances.items():
            try:
                status = await provider.health_check()
                results[provider_id] = status
            except Exception as e:
                logger.error(f"Health check failed for {provider_id}: {e}")
                results[provider_id] = ProviderStatus.UNHEALTHY

        return results

    @classmethod
    async def close_provider(cls, provider_id: UUID) -> None:
        """
        Close and remove a provider instance.

        Args:
            provider_id: Provider to close
        """
        cache_key = str(provider_id)

        if cache_key in cls._instances:
            provider = cls._instances[cache_key]
            try:
                if hasattr(provider, 'close'):
                    await provider.close()
            except Exception as e:
                logger.error(f"Error closing provider {provider_id}: {e}")
            finally:
                del cls._instances[cache_key]
                cls._configs.pop(cache_key, None)

    @classmethod
    async def close_all(cls) -> None:
        """Close all provider instances."""
        for provider_id in list(cls._instances.keys()):
            await cls.close_provider(UUID(provider_id))

    @classmethod
    def get_supported_providers(cls) -> Dict[str, list]:
        """
        Get list of supported providers by channel.

        Returns:
            Dict of channel -> list of provider types
        """
        by_channel = {
            'whatsapp': [],
            'sms': [],
            'email': [],
            'voice': [],
            'push_notification': []
        }

        for provider_type, provider_class in PROVIDER_CLASSES.items():
            if provider_class is None:
                continue

            if 'whatsapp' in provider_type:
                by_channel['whatsapp'].append(provider_type)
            elif provider_type in ['twilio_voice', 'aws_connect']:
                by_channel['voice'].append(provider_type)
            elif provider_type in ['sendgrid', 'aws_ses']:
                by_channel['email'].append(provider_type)
            elif provider_type == 'firebase_push':
                by_channel['push_notification'].append(provider_type)
            else:
                by_channel['sms'].append(provider_type)

        return by_channel

    @classmethod
    def get_default_provider_type(cls, channel: str) -> Optional[str]:
        """
        Get default provider type for a channel.

        Args:
            channel: Channel name

        Returns:
            Default provider type for the channel
        """
        return CHANNEL_DEFAULT_PROVIDERS.get(channel)


def get_provider(
    provider_id: UUID,
    provider_type: str,
    config: Dict[str, Any]
) -> Optional[BaseChannelProvider]:
    """
    Convenience function to get or create a provider.

    Args:
        provider_id: Provider identifier
        provider_type: Type of provider
        config: Provider configuration

    Returns:
        Provider instance
    """
    return ProviderFactory.get_or_create(provider_id, provider_type, config)
