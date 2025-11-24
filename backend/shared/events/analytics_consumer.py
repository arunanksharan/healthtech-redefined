"""
Event Analytics Consumer
Streams events from Kafka to Elasticsearch for real-time analytics
"""
import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch
from loguru import logger

from .consumer import EventConsumer
from .types import Event, EventType


class EventAnalyticsConsumer:
    """
    Consumes events from Kafka and indexes them in Elasticsearch

    Features:
    - Real-time event streaming to Elasticsearch
    - Automatic index creation with mappings
    - Batch indexing for performance
    - Error handling and retry
    - Pattern detection and anomaly alerts
    """

    def __init__(
        self,
        elasticsearch_hosts: Optional[List[str]] = None,
        index_prefix: str = "healthtech-events",
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        """
        Initialize analytics consumer

        Args:
            elasticsearch_hosts: List of Elasticsearch hosts
            index_prefix: Prefix for Elasticsearch indices
            batch_size: Number of events to batch before indexing
            flush_interval: Maximum seconds between flushes
        """
        self.es_hosts = elasticsearch_hosts or [
            os.getenv("ELASTICSEARCH_HOSTS", "http://localhost:9200")
        ]
        self.index_prefix = index_prefix
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self.es_client: Optional[AsyncElasticsearch] = None
        self.batch: List[Dict[str, Any]] = []
        self.consumer: Optional[EventConsumer] = None
        self._running = False

    async def start(self):
        """Start the analytics consumer"""
        # Initialize Elasticsearch client
        self.es_client = AsyncElasticsearch(self.es_hosts)

        # Verify connection
        try:
            info = await self.es_client.info()
            logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            return

        # Create index templates
        await self._create_index_templates()

        # Create Kafka consumer
        self.consumer = EventConsumer(
            group_id="event-analytics-consumer",
            topics=["healthtech.*.events"],
            auto_offset_reset="latest",
        )

        # Register handler for all event types
        for event_type in EventType:
            self.consumer.register_handler(event_type, self._handle_event)

        logger.info("Event analytics consumer started")

        # Start auto-flush task
        self._running = True
        flush_task = asyncio.create_task(self._auto_flush_loop())

        # Start consuming
        try:
            await self.consumer.start()
        finally:
            self._running = False
            flush_task.cancel()
            await self._flush_batch()
            await self.es_client.close()

    async def _create_index_templates(self):
        """Create Elasticsearch index templates for events"""
        template_body = {
            "index_patterns": [f"{self.index_prefix}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1,
                    "refresh_interval": "5s",
                },
                "mappings": {
                    "properties": {
                        "event_id": {"type": "keyword"},
                        "event_type": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},
                        "occurred_at": {"type": "date"},
                        "source_service": {"type": "keyword"},
                        "source_user_id": {"type": "keyword"},
                        "aggregate_type": {"type": "keyword"},
                        "aggregate_id": {"type": "keyword"},
                        "payload": {"type": "object", "enabled": True},
                        "metadata": {"type": "object", "enabled": True},
                        # Analytics fields
                        "indexed_at": {"type": "date"},
                        "processing_time_ms": {"type": "float"},
                        "event_domain": {"type": "keyword"},
                        "event_action": {"type": "keyword"},
                    }
                },
            },
        }

        try:
            await self.es_client.indices.put_index_template(
                name=f"{self.index_prefix}-template",
                body=template_body,
            )
            logger.info("Elasticsearch index template created")
        except Exception as e:
            logger.error(f"Failed to create index template: {e}")

    async def _handle_event(self, event: Event):
        """
        Handle incoming event by adding to batch

        Args:
            event: Event to process
        """
        # Extract domain and action from event type
        event_parts = event.event_type.value.split(".")
        domain = event_parts[0] if len(event_parts) > 0 else "Unknown"
        action = event_parts[1] if len(event_parts) > 1 else "Unknown"

        # Prepare document for indexing
        doc = {
            "event_id": str(event.event_id),
            "event_type": event.event_type.value,
            "tenant_id": event.tenant_id,
            "occurred_at": event.occurred_at.isoformat(),
            "source_service": event.source_service,
            "source_user_id": str(event.source_user_id) if event.source_user_id else None,
            "payload": event.payload,
            "metadata": event.metadata,
            # Analytics fields
            "indexed_at": datetime.utcnow().isoformat(),
            "event_domain": domain,
            "event_action": action,
        }

        # Extract aggregate info if present
        if "patient_id" in event.payload:
            doc["aggregate_type"] = "Patient"
            doc["aggregate_id"] = event.payload["patient_id"]
        elif "appointment_id" in event.payload:
            doc["aggregate_type"] = "Appointment"
            doc["aggregate_id"] = event.payload["appointment_id"]

        self.batch.append(doc)

        # Flush if batch is full
        if len(self.batch) >= self.batch_size:
            await self._flush_batch()

    async def _flush_batch(self):
        """Flush accumulated events to Elasticsearch"""
        if not self.batch or not self.es_client:
            return

        batch_to_index = self.batch.copy()
        self.batch.clear()

        try:
            # Get index name based on date
            index_name = f"{self.index_prefix}-{datetime.utcnow().strftime('%Y.%m.%d')}"

            # Bulk index
            operations = []
            for doc in batch_to_index:
                operations.append({"index": {"_index": index_name}})
                operations.append(doc)

            response = await self.es_client.bulk(operations=operations)

            if response.get("errors"):
                logger.error(f"Bulk indexing had errors: {response}")
            else:
                logger.debug(
                    f"Indexed {len(batch_to_index)} events to {index_name}"
                )

        except Exception as e:
            logger.error(f"Failed to flush batch to Elasticsearch: {e}")
            # Add events back to batch for retry
            self.batch.extend(batch_to_index)

    async def _auto_flush_loop(self):
        """Auto-flush events on interval"""
        while self._running:
            await asyncio.sleep(self.flush_interval)
            if self.batch:
                await self._flush_batch()

    async def get_event_stats(
        self, tenant_id: str, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get event statistics for tenant

        Args:
            tenant_id: Tenant identifier
            hours: Number of hours to look back

        Returns:
            Statistics dictionary
        """
        if not self.es_client:
            return {}

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"tenant_id": tenant_id}},
                        {
                            "range": {
                                "occurred_at": {
                                    "gte": f"now-{hours}h",
                                    "lte": "now",
                                }
                            }
                        },
                    ]
                }
            },
            "aggs": {
                "events_by_type": {
                    "terms": {"field": "event_type", "size": 50}
                },
                "events_by_domain": {
                    "terms": {"field": "event_domain", "size": 20}
                },
                "events_over_time": {
                    "date_histogram": {
                        "field": "occurred_at",
                        "calendar_interval": "hour",
                    }
                },
            },
        }

        try:
            result = await self.es_client.search(
                index=f"{self.index_prefix}-*", body=query, size=0
            )

            return {
                "total_events": result["hits"]["total"]["value"],
                "by_type": [
                    {
                        "event_type": bucket["key"],
                        "count": bucket["doc_count"],
                    }
                    for bucket in result["aggregations"]["events_by_type"]["buckets"]
                ],
                "by_domain": [
                    {
                        "domain": bucket["key"],
                        "count": bucket["doc_count"],
                    }
                    for bucket in result["aggregations"]["events_by_domain"]["buckets"]
                ],
                "over_time": [
                    {
                        "timestamp": bucket["key_as_string"],
                        "count": bucket["doc_count"],
                    }
                    for bucket in result["aggregations"]["events_over_time"]["buckets"]
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get event stats: {e}")
            return {}

    async def detect_anomalies(
        self, tenant_id: str, threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous event patterns

        Args:
            tenant_id: Tenant identifier
            threshold: Standard deviations from mean

        Returns:
            List of anomalies detected
        """
        # Simplified anomaly detection
        # In production, use proper ML models
        stats = await self.get_event_stats(tenant_id, hours=24)

        anomalies = []
        if "over_time" in stats:
            counts = [bucket["count"] for bucket in stats["over_time"]]
            if counts:
                mean = sum(counts) / len(counts)
                std = (sum((x - mean) ** 2 for x in counts) / len(counts)) ** 0.5

                for bucket in stats["over_time"]:
                    if abs(bucket["count"] - mean) > (threshold * std):
                        anomalies.append(
                            {
                                "timestamp": bucket["timestamp"],
                                "count": bucket["count"],
                                "expected": mean,
                                "deviation": (bucket["count"] - mean) / std,
                                "severity": "high" if abs(bucket["count"] - mean) > (5 * std) else "medium",
                            }
                        )

        return anomalies


# Standalone script to run analytics consumer
async def main():
    """Run event analytics consumer"""
    consumer = EventAnalyticsConsumer()

    logger.info("Starting event analytics consumer...")
    logger.info("Elasticsearch: http://localhost:9200")
    logger.info("Kibana: http://localhost:5601")

    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down analytics consumer...")
    except Exception as e:
        logger.error(f"Analytics consumer error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
