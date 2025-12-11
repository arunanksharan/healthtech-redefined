"""
Kafka Cluster Configuration

Comprehensive Kafka cluster configuration including:
- Topic management and creation
- Producer/consumer configuration
- Security settings (SSL, SASL)
- Monitoring and health checks
- Performance tuning

EPIC-002: US-002.1 Kafka Cluster Setup
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource, ResourceType
from confluent_kafka import KafkaException

logger = logging.getLogger(__name__)


class CompressionType(str, Enum):
    """Kafka message compression types."""
    NONE = "none"
    GZIP = "gzip"
    SNAPPY = "snappy"
    LZ4 = "lz4"
    ZSTD = "zstd"


class AcksMode(str, Enum):
    """Producer acknowledgment modes."""
    NONE = "0"  # No acks (fastest, least durable)
    LEADER = "1"  # Leader ack only
    ALL = "all"  # All replicas ack (slowest, most durable)


class IsolationLevel(str, Enum):
    """Consumer isolation levels."""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"


@dataclass
class TopicConfig:
    """Configuration for a Kafka topic."""
    name: str
    partitions: int = 12
    replication_factor: int = 3
    retention_ms: int = 2592000000  # 30 days
    retention_bytes: int = -1  # Unlimited
    cleanup_policy: str = "delete"  # delete or compact
    min_insync_replicas: int = 2
    segment_ms: int = 86400000  # 1 day
    segment_bytes: int = 1073741824  # 1GB
    compression_type: str = "gzip"
    max_message_bytes: int = 1048576  # 1MB

    def to_config_dict(self) -> Dict[str, str]:
        """Convert to Kafka config dictionary."""
        return {
            "retention.ms": str(self.retention_ms),
            "retention.bytes": str(self.retention_bytes),
            "cleanup.policy": self.cleanup_policy,
            "min.insync.replicas": str(self.min_insync_replicas),
            "segment.ms": str(self.segment_ms),
            "segment.bytes": str(self.segment_bytes),
            "compression.type": self.compression_type,
            "max.message.bytes": str(self.max_message_bytes),
        }


@dataclass
class ProducerConfig:
    """Producer configuration."""
    bootstrap_servers: str
    client_id: str = "healthtech-producer"
    acks: AcksMode = AcksMode.ALL
    retries: int = 3
    retry_backoff_ms: int = 100
    max_in_flight_requests: int = 5
    compression_type: CompressionType = CompressionType.GZIP
    linger_ms: int = 10
    batch_size: int = 16384
    buffer_memory: int = 33554432  # 32MB
    request_timeout_ms: int = 30000
    enable_idempotence: bool = True

    # Security settings
    security_protocol: str = "PLAINTEXT"  # PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
    ssl_ca_location: Optional[str] = None
    ssl_certificate_location: Optional[str] = None
    ssl_key_location: Optional[str] = None
    sasl_mechanism: Optional[str] = None  # PLAIN, SCRAM-SHA-256, SCRAM-SHA-512
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to Kafka config dictionary."""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": self.client_id,
            "acks": self.acks.value,
            "retries": self.retries,
            "retry.backoff.ms": self.retry_backoff_ms,
            "max.in.flight.requests.per.connection": self.max_in_flight_requests,
            "compression.type": self.compression_type.value,
            "linger.ms": self.linger_ms,
            "batch.size": self.batch_size,
            "buffer.memory": self.buffer_memory,
            "request.timeout.ms": self.request_timeout_ms,
            "enable.idempotence": self.enable_idempotence,
            "security.protocol": self.security_protocol,
        }

        # Add SSL settings if configured
        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_certificate_location:
            config["ssl.certificate.location"] = self.ssl_certificate_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location

        # Add SASL settings if configured
        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            config["sasl.username"] = self.sasl_username
        if self.sasl_password:
            config["sasl.password"] = self.sasl_password

        return config


@dataclass
class ConsumerConfig:
    """Consumer configuration."""
    bootstrap_servers: str
    group_id: str
    client_id: str = "healthtech-consumer"
    auto_offset_reset: str = "earliest"  # earliest, latest, none
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    session_timeout_ms: int = 45000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    max_poll_records: int = 500
    fetch_min_bytes: int = 1
    fetch_max_wait_ms: int = 500
    fetch_max_bytes: int = 52428800  # 50MB
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED

    # Security settings (same as producer)
    security_protocol: str = "PLAINTEXT"
    ssl_ca_location: Optional[str] = None
    ssl_certificate_location: Optional[str] = None
    ssl_key_location: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to Kafka config dictionary."""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "client.id": self.client_id,
            "auto.offset.reset": self.auto_offset_reset,
            "enable.auto.commit": self.enable_auto_commit,
            "auto.commit.interval.ms": self.auto_commit_interval_ms,
            "session.timeout.ms": self.session_timeout_ms,
            "heartbeat.interval.ms": self.heartbeat_interval_ms,
            "max.poll.interval.ms": self.max_poll_interval_ms,
            "max.poll.records": self.max_poll_records,
            "fetch.min.bytes": self.fetch_min_bytes,
            "fetch.max.wait.ms": self.fetch_max_wait_ms,
            "fetch.max.bytes": self.fetch_max_bytes,
            "isolation.level": self.isolation_level.value,
            "security.protocol": self.security_protocol,
        }

        # Add SSL settings if configured
        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_certificate_location:
            config["ssl.certificate.location"] = self.ssl_certificate_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location

        # Add SASL settings if configured
        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            config["sasl.username"] = self.sasl_username
        if self.sasl_password:
            config["sasl.password"] = self.sasl_password

        return config


# Healthcare-specific topic definitions
HEALTHCARE_TOPICS: List[TopicConfig] = [
    # Patient events - high volume, long retention
    TopicConfig(
        name="healthtech.patient.events",
        partitions=12,
        replication_factor=3,
        retention_ms=2592000000,  # 30 days
        min_insync_replicas=2,
    ),
    # Appointment events - medium volume
    TopicConfig(
        name="healthtech.appointment.events",
        partitions=12,
        replication_factor=3,
        retention_ms=2592000000,  # 30 days
        min_insync_replicas=2,
    ),
    # Encounter/clinical events - high volume, long retention
    TopicConfig(
        name="healthtech.encounter.events",
        partitions=24,
        replication_factor=3,
        retention_ms=7776000000,  # 90 days
        min_insync_replicas=2,
    ),
    # Journey/PRM events
    TopicConfig(
        name="healthtech.journey.events",
        partitions=6,
        replication_factor=3,
        retention_ms=2592000000,  # 30 days
        cleanup_policy="compact",  # Keep latest state
        min_insync_replicas=2,
    ),
    # Communication events
    TopicConfig(
        name="healthtech.communication.events",
        partitions=12,
        replication_factor=3,
        retention_ms=604800000,  # 7 days
        min_insync_replicas=2,
    ),
    # Consent events - critical, long retention
    TopicConfig(
        name="healthtech.consent.events",
        partitions=6,
        replication_factor=3,
        retention_ms=31536000000,  # 365 days
        cleanup_policy="compact",
        min_insync_replicas=2,
    ),
    # Billing/RCM events
    TopicConfig(
        name="healthtech.billing.events",
        partitions=12,
        replication_factor=3,
        retention_ms=7776000000,  # 90 days
        min_insync_replicas=2,
    ),
    # Order events (lab, imaging, medication)
    TopicConfig(
        name="healthtech.order.events",
        partitions=12,
        replication_factor=3,
        retention_ms=2592000000,  # 30 days
        min_insync_replicas=2,
    ),
    # FHIR resource events
    TopicConfig(
        name="healthtech.fhir.events",
        partitions=12,
        replication_factor=3,
        retention_ms=2592000000,  # 30 days
        min_insync_replicas=2,
    ),
    # System events
    TopicConfig(
        name="healthtech.system.events",
        partitions=6,
        replication_factor=3,
        retention_ms=604800000,  # 7 days
        min_insync_replicas=1,
    ),
    # Dead letter queues
    TopicConfig(
        name="healthtech.dlq.patient",
        partitions=3,
        replication_factor=3,
        retention_ms=604800000,  # 7 days
        min_insync_replicas=2,
    ),
    TopicConfig(
        name="healthtech.dlq.appointment",
        partitions=3,
        replication_factor=3,
        retention_ms=604800000,  # 7 days
        min_insync_replicas=2,
    ),
    TopicConfig(
        name="healthtech.dlq.clinical",
        partitions=3,
        replication_factor=3,
        retention_ms=604800000,  # 7 days
        min_insync_replicas=2,
    ),
]


class KafkaClusterManager:
    """
    Manages Kafka cluster configuration and operations.

    Features:
    - Topic creation and management
    - Cluster health monitoring
    - Configuration updates
    - Performance metrics
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        security_config: Optional[Dict[str, str]] = None,
    ):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.security_config = security_config or {}

        self._admin_client: Optional[AdminClient] = None

    def _get_admin_client(self) -> AdminClient:
        """Get or create admin client."""
        if self._admin_client is None:
            config = {
                "bootstrap.servers": self.bootstrap_servers,
                **self.security_config,
            }
            self._admin_client = AdminClient(config)
        return self._admin_client

    def create_topic(self, topic_config: TopicConfig) -> bool:
        """
        Create a new topic.

        Args:
            topic_config: Topic configuration

        Returns:
            True if created successfully
        """
        admin = self._get_admin_client()

        new_topic = NewTopic(
            topic=topic_config.name,
            num_partitions=topic_config.partitions,
            replication_factor=topic_config.replication_factor,
            config=topic_config.to_config_dict(),
        )

        try:
            futures = admin.create_topics([new_topic])

            for topic, future in futures.items():
                try:
                    future.result()
                    logger.info(f"Created topic: {topic}")
                    return True
                except KafkaException as e:
                    if "TopicExistsException" in str(e):
                        logger.info(f"Topic already exists: {topic}")
                        return True
                    logger.error(f"Failed to create topic {topic}: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error creating topic: {e}")
            return False

    def create_all_healthcare_topics(self) -> Dict[str, bool]:
        """
        Create all healthcare topics.

        Returns:
            Dictionary of topic_name -> success
        """
        results = {}
        for topic_config in HEALTHCARE_TOPICS:
            results[topic_config.name] = self.create_topic(topic_config)
        return results

    def delete_topic(self, topic_name: str) -> bool:
        """Delete a topic."""
        admin = self._get_admin_client()

        try:
            futures = admin.delete_topics([topic_name])

            for topic, future in futures.items():
                try:
                    future.result()
                    logger.info(f"Deleted topic: {topic}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete topic {topic}: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting topic: {e}")
            return False

    def list_topics(self) -> List[str]:
        """List all topics in the cluster."""
        admin = self._get_admin_client()

        try:
            metadata = admin.list_topics(timeout=10)
            return list(metadata.topics.keys())
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            return []

    def get_topic_config(self, topic_name: str) -> Dict[str, str]:
        """Get configuration for a topic."""
        admin = self._get_admin_client()

        try:
            resource = ConfigResource(ResourceType.TOPIC, topic_name)
            futures = admin.describe_configs([resource])

            for resource, future in futures.items():
                config = future.result()
                return {
                    entry.name: entry.value
                    for entry in config.values()
                    if entry.value is not None
                }

        except Exception as e:
            logger.error(f"Error getting topic config: {e}")
            return {}

    def update_topic_config(
        self,
        topic_name: str,
        config_updates: Dict[str, str],
    ) -> bool:
        """Update topic configuration."""
        admin = self._get_admin_client()

        try:
            resource = ConfigResource(
                ResourceType.TOPIC,
                topic_name,
                set_config=config_updates,
            )
            futures = admin.alter_configs([resource])

            for resource, future in futures.items():
                try:
                    future.result()
                    logger.info(f"Updated config for topic: {topic_name}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to update config: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error updating topic config: {e}")
            return False

    def get_cluster_metadata(self) -> Dict[str, Any]:
        """Get cluster metadata and health information."""
        admin = self._get_admin_client()

        try:
            metadata = admin.list_topics(timeout=10)

            brokers = [
                {
                    "id": broker.id,
                    "host": broker.host,
                    "port": broker.port,
                }
                for broker in metadata.brokers.values()
            ]

            topics = []
            for topic_name, topic_metadata in metadata.topics.items():
                if not topic_name.startswith("__"):  # Skip internal topics
                    topics.append({
                        "name": topic_name,
                        "partitions": len(topic_metadata.partitions),
                        "error": str(topic_metadata.error) if topic_metadata.error else None,
                    })

            return {
                "cluster_id": metadata.cluster_id,
                "controller_id": metadata.controller_id,
                "brokers": brokers,
                "topics": topics,
                "topic_count": len([t for t in topics if not t["name"].startswith("__")]),
            }

        except Exception as e:
            logger.error(f"Error getting cluster metadata: {e}")
            return {"error": str(e)}

    def get_consumer_group_offsets(
        self,
        group_id: str,
    ) -> Dict[str, Dict[int, int]]:
        """Get consumer group offsets for all topics."""
        admin = self._get_admin_client()

        try:
            # Get committed offsets
            from confluent_kafka import Consumer

            consumer_config = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
            }
            consumer = Consumer(consumer_config)

            offsets = {}
            topics = self.list_topics()

            for topic in topics:
                if topic.startswith("__"):
                    continue

                try:
                    partitions = consumer.list_topics(topic).topics[topic].partitions
                    topic_offsets = {}

                    for partition_id in partitions:
                        from confluent_kafka import TopicPartition
                        tp = TopicPartition(topic, partition_id)
                        committed = consumer.committed([tp])[0]
                        if committed.offset >= 0:
                            topic_offsets[partition_id] = committed.offset

                    if topic_offsets:
                        offsets[topic] = topic_offsets

                except Exception:
                    pass

            consumer.close()
            return offsets

        except Exception as e:
            logger.error(f"Error getting consumer group offsets: {e}")
            return {}

    def check_cluster_health(self) -> Dict[str, Any]:
        """
        Check cluster health status.

        Returns:
            Health status dictionary
        """
        metadata = self.get_cluster_metadata()

        if "error" in metadata:
            return {
                "healthy": False,
                "error": metadata["error"],
            }

        # Check broker count
        broker_count = len(metadata.get("brokers", []))
        min_brokers = int(os.getenv("KAFKA_MIN_BROKERS", "1"))

        # Check for topic errors
        topics_with_errors = [
            t for t in metadata.get("topics", [])
            if t.get("error")
        ]

        healthy = (
            broker_count >= min_brokers
            and len(topics_with_errors) == 0
        )

        return {
            "healthy": healthy,
            "broker_count": broker_count,
            "min_brokers_required": min_brokers,
            "topic_count": metadata.get("topic_count", 0),
            "topics_with_errors": len(topics_with_errors),
            "controller_id": metadata.get("controller_id"),
            "cluster_id": metadata.get("cluster_id"),
        }


def get_producer_config() -> ProducerConfig:
    """Get producer configuration from environment."""
    return ProducerConfig(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        client_id=os.getenv("KAFKA_CLIENT_ID", "healthtech-producer"),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        ssl_ca_location=os.getenv("KAFKA_SSL_CA_LOCATION"),
        ssl_certificate_location=os.getenv("KAFKA_SSL_CERT_LOCATION"),
        ssl_key_location=os.getenv("KAFKA_SSL_KEY_LOCATION"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
    )


def get_consumer_config(group_id: str) -> ConsumerConfig:
    """Get consumer configuration from environment."""
    return ConsumerConfig(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        group_id=group_id,
        client_id=os.getenv("KAFKA_CLIENT_ID", "healthtech-consumer"),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        ssl_ca_location=os.getenv("KAFKA_SSL_CA_LOCATION"),
        ssl_certificate_location=os.getenv("KAFKA_SSL_CERT_LOCATION"),
        ssl_key_location=os.getenv("KAFKA_SSL_KEY_LOCATION"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
    )


# Global cluster manager
_cluster_manager: Optional[KafkaClusterManager] = None


def get_cluster_manager() -> KafkaClusterManager:
    """Get or create global cluster manager."""
    global _cluster_manager
    if _cluster_manager is None:
        _cluster_manager = KafkaClusterManager()
    return _cluster_manager
