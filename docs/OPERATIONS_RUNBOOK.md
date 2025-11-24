# Event-Driven Architecture - Operations Runbook

## Overview

This runbook provides operational procedures for managing the event-driven architecture in production. It covers deployment, monitoring, troubleshooting, and maintenance tasks.

**Target Audience**: DevOps Engineers, SREs, Platform Team
**Last Updated**: November 24, 2024
**Version**: 1.0

---

## Table of Contents

1. [Deployment](#deployment)
2. [Monitoring](#monitoring)
3. [Troubleshooting](#troubleshooting)
4. [Maintenance](#maintenance)
5. [Disaster Recovery](#disaster-recovery)
6. [Scaling](#scaling)
7. [Security](#security)
8. [Incident Response](#incident-response)

---

## Deployment

### Initial Deployment

```bash
# 1. Clone repository
git clone <repo-url>
cd healthtech-redefined

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with production values

# 3. Start infrastructure
docker-compose up -d kafka-1 kafka-2 kafka-3 zookeeper
docker-compose up -d schema-registry kafka-ui
docker-compose up -d elasticsearch kibana
docker-compose up -d postgres redis
docker-compose up -d prometheus grafana

# 4. Verify infrastructure health
docker-compose ps
./scripts/health-check.sh

# 5. Apply database migrations
cd backend
alembic upgrade head

# 6. Start services
docker-compose up -d prm-service fhir-service identity-service

# 7. Start event consumers
docker-compose up -d event-analytics-consumer

# 8. Verify deployment
./scripts/verify-deployment.sh
```

### Rolling Update

```bash
# 1. Update code
git pull origin main

# 2. Build new images
docker-compose build <service-name>

# 3. Rolling restart (zero downtime)
docker-compose up -d --no-deps --scale <service-name>=2 <service-name>
sleep 30
docker-compose up -d --no-deps --scale <service-name>=1 <service-name>

# 4. Verify health
curl http://localhost:8007/health
```

### Rollback Procedure

```bash
# 1. Identify last good version
git log --oneline

# 2. Checkout previous version
git checkout <commit-hash>

# 3. Rebuild and restart
docker-compose build <service-name>
docker-compose up -d <service-name>

# 4. Verify rollback
./scripts/health-check.sh
```

---

## Monitoring

### Key Metrics to Monitor

#### Kafka Metrics
```promql
# Broker availability
up{job=~"kafka-broker.*"}

# Under-replicated partitions (should be 0)
kafka_server_replicamanager_underreplicatedpartitions

# Message rate
rate(kafka_server_brokertopicmetrics_messagesin_total[5m])

# Consumer lag
kafka_consumergroup_lag{group="prm-service-consumer"}
```

#### Event Metrics
```promql
# Event publishing rate
rate(event_published_total[5m])

# Event publishing latency
histogram_quantile(0.99, rate(event_publish_duration_seconds_bucket[5m]))

# Error rate
rate(event_publish_errors_total[5m]) / rate(event_published_total[5m])

# Consumer lag
sum(consumer_lag_messages) by (consumer_group)

# DLQ size
dlq_messages_total
```

#### Circuit Breaker Status
```promql
# Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
circuit_breaker_state{service="prm-service"}

# Circuit breaker failures
rate(circuit_breaker_failures_total[5m])
```

### Dashboards

#### Grafana Dashboards
- **URL**: http://localhost:3001
- **Login**: admin/admin
- **Dashboard**: "Event-Driven Architecture Metrics"

**Key Panels**:
1. Event Publishing Rate
2. Publishing Latency (p99)
3. Consumer Lag
4. Error Rate
5. DLQ Size
6. Circuit Breaker Status
7. Kafka Broker Health
8. Workflow Execution Rate

#### Kafka UI
- **URL**: http://localhost:8090
- **Features**:
  - View topics and messages
  - Monitor consumer groups
  - Check broker health
  - View schemas

#### Kibana (Event Analytics)
- **URL**: http://localhost:5601
- **Index Pattern**: `healthtech-events-*`
- **Dashboards**: Event patterns, anomalies, business metrics

### Alert Rules

#### Critical Alerts (Page On-Call)

**Consumer Lag High**
```yaml
alert: ConsumerLagHigh
expr: consumer_lag_messages > 1000
for: 5m
severity: critical
description: Consumer lag is {{ $value }} messages
```

**Kafka Broker Down**
```yaml
alert: KafkaBrokerDown
expr: up{job=~"kafka-broker.*"} == 0
for: 1m
severity: critical
description: Kafka broker {{ $labels.instance }} is down
```

**Circuit Breaker Open**
```yaml
alert: CircuitBreakerOpen
expr: circuit_breaker_state == 1
for: 5m
severity: critical
description: Circuit breaker open for {{ $labels.service }}
```

#### Warning Alerts (Notify Slack)

**High Error Rate**
```yaml
alert: HighErrorRate
expr: rate(event_publish_errors_total[5m]) / rate(event_published_total[5m]) > 0.01
for: 10m
severity: warning
```

**DLQ Growing**
```yaml
alert: DLQGrowing
expr: dlq_messages_total > 100
for: 15m
severity: warning
```

---

## Troubleshooting

### Common Issues

#### 1. High Consumer Lag

**Symptoms**: Consumer lag > 1000 messages

**Diagnosis**:
```bash
# Check consumer lag
docker-compose exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group prm-service-consumer

# Check consumer logs
docker-compose logs --tail=100 prm-service
```

**Resolution**:
```bash
# Option 1: Scale up consumers
docker-compose up -d --scale prm-service=3

# Option 2: Increase consumer parallelism
# Edit consumer configuration: max_poll_records=500

# Option 3: Optimize consumer handler
# Profile slow handlers and optimize
```

#### 2. Events Not Being Published

**Symptoms**: Event publishing failures, circuit breaker open

**Diagnosis**:
```bash
# Check Kafka cluster health
docker-compose ps kafka-1 kafka-2 kafka-3

# Check broker logs
docker-compose logs kafka-1 | grep ERROR

# Verify topics exist
docker-compose exec kafka-1 kafka-topics --list --bootstrap-server localhost:9092
```

**Resolution**:
```bash
# Restart Kafka brokers one by one
docker-compose restart kafka-1
sleep 30
docker-compose restart kafka-2
sleep 30
docker-compose restart kafka-3

# Reset circuit breaker if stuck
curl -X POST http://localhost:8007/admin/circuit-breaker/reset
```

#### 3. Events Not Being Consumed

**Symptoms**: Events in topic but not processed

**Diagnosis**:
```bash
# Check if consumer is running
docker-compose ps prm-service

# Check consumer group membership
docker-compose exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group prm-service-consumer

# Check consumer logs
docker-compose logs prm-service | grep ERROR
```

**Resolution**:
```bash
# Restart consumer
docker-compose restart prm-service

# If offset stuck, reset to latest
docker-compose exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group prm-service-consumer \
  --topic healthtech.patient.events \
  --reset-offsets --to-latest --execute
```

#### 4. High Latency

**Symptoms**: p99 latency > 50ms

**Diagnosis**:
```bash
# Check Kafka broker CPU/memory
docker stats kafka-1 kafka-2 kafka-3

# Check network latency
ping kafka-1

# Check slow handlers
docker-compose logs prm-service | grep "slow"
```

**Resolution**:
```bash
# Increase batch size for throughput
# Edit: publisher.py -> batch_size=200

# Enable compression
# Edit: producer config -> compression.type=gzip

# Optimize slow handlers
# Profile and optimize database queries
```

#### 5. DLQ Growing

**Symptoms**: Failed events accumulating in DLQ

**Diagnosis**:
```bash
# Check DLQ topics
docker-compose exec kafka-1 kafka-topics \
  --list --bootstrap-server localhost:9092 | grep dlq

# View failed events
curl http://localhost:9200/healthtech-dlq-*/_search?size=10

# Check error patterns
docker-compose logs prm-service | grep "DLQ"
```

**Resolution**:
```bash
# 1. Identify root cause from error logs
# 2. Fix the bug in consumer handler
# 3. Deploy fix
# 4. Replay failed events
python scripts/replay_dlq_events.py --topic healthtech.dlq.patient --from-date 2024-11-24
```

### Debug Commands

```bash
# View Kafka topics
docker-compose exec kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# View messages in topic
docker-compose exec kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic healthtech.patient.events \
  --from-beginning --max-messages 10

# Check consumer group status
docker-compose exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --all-groups

# View Elasticsearch indices
curl http://localhost:9200/_cat/indices?v

# Query recent events
curl "http://localhost:9200/healthtech-events-*/_search?size=10&sort=occurred_at:desc"

# Check circuit breaker status
curl http://localhost:8007/admin/circuit-breaker/status

# View Prometheus targets
curl http://localhost:9090/api/v1/targets

# View Grafana health
curl http://localhost:3001/api/health
```

---

## Maintenance

### Daily Tasks

```bash
# Check system health
./scripts/health-check.sh

# Review error logs
docker-compose logs --since 24h | grep ERROR

# Check DLQ size
curl http://localhost:9200/healthtech-dlq-*/_count

# Verify consumer lag < 100
curl http://localhost:9090/api/v1/query?query=consumer_lag_messages
```

### Weekly Tasks

```bash
# Review performance metrics
# - Check Grafana dashboards
# - Review p99 latencies
# - Check error rates

# Clean up old Elasticsearch indices (>30 days)
curl -X DELETE "http://localhost:9200/healthtech-events-$(date -d '30 days ago' +%Y.%m.%d)"

# Review and resolve failed events in DLQ
python scripts/review_dlq.py --last-7-days

# Check disk usage
df -h
docker system df
```

### Monthly Tasks

```bash
# Kafka cluster maintenance
# - Check broker logs for errors
# - Review replication status
# - Optimize topic configurations

# Database maintenance
# - Vacuum event store tables
psql -c "VACUUM ANALYZE stored_events;"
psql -c "VACUUM ANALYZE aggregate_snapshots;"

# Backup event store
pg_dump -t stored_events -t aggregate_snapshots > backup_$(date +%Y%m%d).sql

# Review and update dashboards
# - Add new metrics
# - Update alert thresholds
# - Add business metrics

# Security updates
# - Update Docker images
# - Apply security patches
```

---

## Disaster Recovery

### Backup Procedures

#### Kafka Topics Backup
```bash
# Backup all topics
docker-compose exec kafka-1 kafka-mirror-maker \
  --consumer.config consumer.properties \
  --producer.config producer.properties \
  --whitelist="healthtech.*"
```

#### Event Store Backup
```bash
# Daily backup
pg_dump -U postgres -h localhost healthtech \
  -t stored_events \
  -t aggregate_snapshots \
  -t failed_events \
  | gzip > backup_$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://backups/event-store/
```

#### Elasticsearch Backup
```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/healthtech_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/backups/elasticsearch"
  }
}'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/healthtech_backup/snapshot_$(date +%Y%m%d)"
```

### Recovery Procedures

#### Restore Kafka Cluster
```bash
# 1. Stop all brokers
docker-compose stop kafka-1 kafka-2 kafka-3

# 2. Restore data volumes
docker cp backup/kafka-1-data kafka-1:/var/lib/kafka/data

# 3. Start brokers
docker-compose up -d kafka-1
sleep 30
docker-compose up -d kafka-2 kafka-3

# 4. Verify cluster
docker-compose exec kafka-1 kafka-topics --list --bootstrap-server localhost:9092
```

#### Restore Event Store
```bash
# 1. Stop services
docker-compose stop prm-service fhir-service

# 2. Restore database
gunzip -c backup_20241124.sql.gz | psql -U postgres healthtech

# 3. Verify restore
psql -U postgres healthtech -c "SELECT COUNT(*) FROM stored_events;"

# 4. Start services
docker-compose up -d prm-service fhir-service
```

#### Event Replay
```bash
# Replay events from event store
python scripts/replay_events.py \
  --tenant-id hospital-1 \
  --from-date 2024-11-20 \
  --to-date 2024-11-24 \
  --event-types Patient.Created,Appointment.Created

# Monitor replay progress
tail -f logs/replay.log
```

---

## Scaling

### Horizontal Scaling

#### Scale Kafka Brokers
```bash
# Add new broker
# 1. Update docker-compose.yml with kafka-4
# 2. Start new broker
docker-compose up -d kafka-4

# 3. Reassign partitions
docker-compose exec kafka-1 kafka-reassign-partitions \
  --bootstrap-server localhost:9092 \
  --topics-to-move-json-file topics.json \
  --broker-list "1,2,3,4" \
  --generate

# 4. Execute reassignment
docker-compose exec kafka-1 kafka-reassign-partitions \
  --bootstrap-server localhost:9092 \
  --reassignment-json-file reassignment.json \
  --execute
```

#### Scale Consumers
```bash
# Scale up consumers (automatic load balancing)
docker-compose up -d --scale prm-service=3

# Verify consumer group members
docker-compose exec kafka-1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group prm-service-consumer
```

#### Scale Elasticsearch
```bash
# Add new Elasticsearch node
# Update docker-compose.yml with elasticsearch-2
docker-compose up -d elasticsearch-2

# Verify cluster
curl http://localhost:9200/_cluster/health
```

### Vertical Scaling

```bash
# Increase Kafka broker resources
# Edit docker-compose.yml:
kafka-1:
  environment:
    - "KAFKA_HEAP_OPTS=-Xms2g -Xmx2g"
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G

# Restart broker
docker-compose up -d kafka-1
```

---

## Security

### Access Control

```bash
# Enable SASL authentication
# Edit docker-compose.yml:
kafka-1:
  environment:
    - KAFKA_SASL_ENABLED_MECHANISMS=PLAIN
    - KAFKA_SASL_MECHANISM_INTER_BROKER_PROTOCOL=PLAIN

# Create users
docker-compose exec kafka-1 kafka-configs \
  --zookeeper zookeeper:2181 \
  --alter --add-config 'SCRAM-SHA-256=[password=secret]' \
  --entity-type users --entity-name prm-service
```

### Encryption

```bash
# Enable SSL/TLS
# 1. Generate certificates
./scripts/generate-certs.sh

# 2. Update Kafka configuration
# listeners=SSL://kafka-1:9093
# ssl.keystore.location=/certs/kafka.server.keystore.jks
```

### Audit Logging

```bash
# Enable audit logging in application
# Edit event publisher:
publish_event(
  event_type=EventType.PATIENT_CREATED,
  metadata={
    "user_id": current_user.id,
    "ip_address": request.client.host,
    "action": "create_patient"
  }
)

# Query audit logs
curl "http://localhost:9200/healthtech-events-*/_search" -d '{
  "query": {
    "term": {"metadata.user_id": "user-123"}
  }
}'
```

---

## Incident Response

### Severity Levels

| Level | Response Time | Escalation |
|-------|--------------|------------|
| **P0 - Critical** | 15 minutes | Page on-call immediately |
| **P1 - High** | 1 hour | Notify team lead |
| **P2 - Medium** | 4 hours | Notify during business hours |
| **P3 - Low** | Next business day | Create ticket |

### Incident Checklist

**P0 Incident Response**:
1. [ ] Acknowledge alert
2. [ ] Assess impact and severity
3. [ ] Create incident channel (#incident-YYYYMMDD)
4. [ ] Notify stakeholders
5. [ ] Begin investigation
6. [ ] Implement mitigation
7. [ ] Monitor resolution
8. [ ] Post-mortem within 48 hours

### Common P0 Incidents

#### Kafka Cluster Down
```bash
# 1. Check broker status
docker-compose ps kafka-1 kafka-2 kafka-3

# 2. Check logs
docker-compose logs kafka-1 | tail -100

# 3. Restart brokers one at a time
docker-compose restart kafka-1
# Wait for recovery
docker-compose restart kafka-2
docker-compose restart kafka-3

# 4. Verify cluster health
docker-compose exec kafka-1 kafka-topics --describe --bootstrap-server localhost:9092
```

#### Data Loss Detected
```bash
# 1. Stop all publishers immediately
docker-compose stop prm-service fhir-service

# 2. Verify event store integrity
psql -c "SELECT COUNT(*) FROM stored_events WHERE occurred_at > NOW() - INTERVAL '1 hour';"

# 3. Check Kafka topic retention
docker-compose exec kafka-1 kafka-topics --describe --topic healthtech.patient.events

# 4. Initiate recovery procedure
python scripts/verify_data_integrity.py

# 5. Restore from backup if necessary
./scripts/restore_from_backup.sh --date 2024-11-24
```

---

## Appendix

### Useful Commands Cheatsheet

```bash
# Kafka
kafka-topics --list                    # List all topics
kafka-consumer-groups --list           # List consumer groups
kafka-console-consumer                 # View messages
kafka-consumer-groups --describe       # Check lag

# Docker
docker-compose ps                      # List services
docker-compose logs -f <service>       # Follow logs
docker-compose restart <service>       # Restart service
docker-compose scale <service>=3       # Scale service

# Elasticsearch
curl localhost:9200/_cat/indices       # List indices
curl localhost:9200/_cat/health        # Cluster health
curl localhost:9200/<index>/_search    # Search index

# Postgres
psql -c "SELECT COUNT(*) FROM stored_events;"
psql -c "SELECT * FROM failed_events LIMIT 10;"

# Metrics
curl localhost:9090/api/v1/query?query=<promql>
```

### Contact Information

- **On-Call Engineer**: [PagerDuty rotation]
- **Platform Team Lead**: platform-lead@healthtech.com
- **DevOps Team**: devops@healthtech.com
- **Slack Channel**: #event-driven-arch

### Related Documentation

- [Architecture Guide](./EVENT_DRIVEN_ARCHITECTURE_GUIDE.md)
- [Event Catalog](./EVENT_CATALOG.md)
- [Quick Start](./QUICK_START_EVENT_DRIVEN.md)
- [Implementation Summary](./EPIC-002-IMPLEMENTATION-SUMMARY.md)

---

**Document Version**: 1.0
**Last Updated**: November 24, 2024
**Maintained By**: Platform Team
**Review Cycle**: Monthly
