# HealthTech Platform - Port Reference

> Complete port allocation guide for all services

## Port Allocation Summary

### Reserved Port Ranges

| Range | Purpose |
|-------|---------|
| 2181-2199 | Zookeeper |
| 3000-3010 | Frontend Applications |
| 5432-5450 | PostgreSQL |
| 5601 | Kibana |
| 6379-6389 | Redis |
| 8001-8099 | Backend Microservices |
| 9090-9099 | Monitoring (Prometheus) |
| 9200-9300 | Elasticsearch |

---

## Infrastructure Services

| Service | Port | Protocol | Internal Name | Description |
|---------|------|----------|---------------|-------------|
| **PostgreSQL** | 5432 | TCP | `postgres` | Primary database |
| **Redis** | 6379 | TCP | `redis` | Cache & sessions |
| **Zookeeper** | 2181 | TCP | `zookeeper` | Kafka coordination |
| **Kafka Broker 1** | 9092 | TCP | `kafka-1` | Message broker (external) |
| **Kafka Broker 1** | 19092 | TCP | `kafka-1` | Message broker (internal) |
| **Kafka Broker 2** | 9094 | TCP | `kafka-2` | Message broker (external) |
| **Kafka Broker 2** | 19094 | TCP | `kafka-2` | Message broker (internal) |
| **Kafka Broker 3** | 9095 | TCP | `kafka-3` | Message broker (external) |
| **Kafka Broker 3** | 19095 | TCP | `kafka-3` | Message broker (internal) |
| **Schema Registry** | 8081 | HTTP | `schema-registry` | Kafka schema management |

---

## Backend Microservices

### Core Services (Phase 1)

| Service | Port | Internal Name | Health Check | Description |
|---------|------|---------------|--------------|-------------|
| **Identity Service** | 8001 | `identity-service` | `/health` | User identity management |
| **FHIR Service** | 8002 | `fhir-service` | `/health` | FHIR R4 data store |
| **Consent Service** | 8003 | `consent-service` | `/health` | Patient consent management |
| **Auth Service** | 8004 | `auth-service` | `/health` | Authentication & JWT |
| **Scheduling Service** | 8005 | `scheduling-service` | `/health` | Appointment scheduling |
| **Encounter Service** | 8006 | `encounter-service` | `/health` | Clinical encounters |
| **PRM Service** | 8007 | `prm-service` | `/health` | Patient Relationship Management |
| **Scribe Service** | 8008 | `scribe-service` | `/health` | AI clinical documentation |
| **Bed Management** | 8009 | `bed-service` | `/health` | Hospital bed allocation |
| **Admission Service** | 8010 | `admission-service` | `/health` | Patient admission |
| **Nursing Service** | 8011 | `nursing-service` | `/health` | Nursing workflows |
| **Orders Service** | 8012 | `orders-service` | `/health` | Lab/imaging orders |
| **ICU Service** | 8013 | `icu-service` | `/health` | ICU monitoring |

### Extended Services (Phase 2+)

| Service | Port | Category | Description |
|---------|------|----------|-------------|
| **Lab Order Service** | 8014 | Laboratory | Lab order management |
| **Specimen Tracking** | 8015 | Laboratory | Specimen lifecycle |
| **Lab Catalog** | 8016 | Laboratory | Test catalog |
| **Lab Result Service** | 8017 | Laboratory | Result processing |
| **Lab AI Orchestrator** | 8018 | Laboratory | AI for lab analytics |
| **PACS Connector** | 8019 | Imaging | DICOM integration |
| **Radiology Worklist** | 8020 | Imaging | Modality worklist |
| **Radiology Reporting** | 8021 | Imaging | Report generation |
| **Imaging AI Orchestrator** | 8022 | Imaging | AI for imaging |
| **Pharmacy Inventory** | 8023 | Pharmacy | Medication inventory |
| **Pharmacy Verification** | 8024 | Pharmacy | Order verification |
| **MAR Service** | 8025 | Pharmacy | Medication administration |
| **Pharmacy AI Orchestrator** | 8026 | Pharmacy | AI for pharmacy |
| **Medication Order** | 8027 | Medication | Prescription management |
| **Medication Catalog** | 8028 | Medication | Drug database |
| **Med Reconciliation** | 8029 | Medication | Medication reconciliation |
| **Coverage Policy** | 8030 | Revenue | Insurance policies |
| **Payer Master** | 8031 | Revenue | Payer management |
| **Tariff Pricebook** | 8032 | Revenue | Pricing management |
| **Billing Service** | 8033 | Revenue | Claims & billing |
| **Analytics Service** | 8034 | Analytics | Core analytics |
| **Analytics Hub** | 8035 | Analytics | Analytics aggregation |
| **Outcomes Service** | 8036 | Analytics | Outcome tracking |
| **Quality Metrics** | 8037 | Analytics | Quality measures |
| **Risk Stratification** | 8038 | Clinical Intel | Patient risk analysis |
| **Knowledge Graph** | 8039 | Clinical Intel | Medical knowledge base |
| **Guideline Engine** | 8040 | Clinical Intel | Clinical guidelines |
| **Voice Collaboration** | 8041 | Communication | Voice integration |
| **Referral Network** | 8042 | Communication | Provider referrals |
| **Remote Monitoring** | 8043 | Communication | RPM integration |
| **Governance Service** | 8044 | Governance | Data governance |
| **Governance Audit** | 8045 | Governance | Audit logging |
| **Deidentification** | 8046 | Governance | PHI anonymization |
| **Interop Gateway** | 8047 | Integration | External integrations |
| **Research Registry** | 8048 | Research | Clinical research |
| **Trial Management** | 8049 | Research | Clinical trials |
| **Synthetic Data** | 8050 | Research | Test data generation |

---

## Frontend Applications

| Application | Port | Framework | Description |
|-------------|------|-----------|-------------|
| **PRM Dashboard** | 3000 | Next.js 15 | Primary web application |
| **Admin Console** | 3001 | Next.js | System administration |
| **Patient Portal** | 3002 | Next.js | Patient self-service |
| **Doctor Portal** | 3003 | Next.js | Physician interface |
| **Nurse Portal** | 3004 | Next.js | Nursing interface |
| **Contact Center** | 3005 | Next.js | Call center interface |

> **Note**: Grafana uses port 3001 in development. For production, reassign as needed.

---

## Monitoring & Observability

| Service | Port | Protocol | Default Credentials | Description |
|---------|------|----------|---------------------|-------------|
| **Prometheus** | 9090 | HTTP | - | Metrics collection |
| **Grafana** | 3001* | HTTP | admin/admin | Dashboards |
| **Elasticsearch** | 9200 | HTTP | - | Search & analytics |
| **Elasticsearch** | 9300 | TCP | - | Cluster communication |
| **Kibana** | 5601 | HTTP | - | Log visualization |
| **Kafka UI** | 8090 | HTTP | - | Kafka management |
| **pgAdmin** | 5050 | HTTP | admin@healthtech.com/admin | Database admin |

*Grafana uses 3001 to avoid conflict with Next.js default port

---

## External Service Endpoints

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **LiveKit** | 443 | WSS | Video/voice calls |
| **Twilio** | 443 | HTTPS | SMS/WhatsApp |
| **OpenAI** | 443 | HTTPS | AI/LLM |
| **AWS S3** | 443 | HTTPS | File storage |
| **Sentry** | 443 | HTTPS | Error tracking |

---

## Docker Network Configuration

```yaml
networks:
  healthtech-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Internal DNS Names

Within the Docker network, services can be reached by their container names:

```
postgres:5432
redis:6379
kafka-1:19092
kafka-2:19094
kafka-3:19095
prm-service:8007
auth-service:8004
```

---

## Port Conflict Resolution

### Common Conflicts

| Conflict | Resolution |
|----------|------------|
| Port 3000 (Next.js vs other apps) | Use different ports: 3000, 3002, 3003 |
| Port 3001 (Grafana vs Admin Console) | Move Admin Console to 3006 |
| Port 5432 (local PostgreSQL) | Stop local PostgreSQL or use 5433 |
| Port 6379 (local Redis) | Stop local Redis or use 6380 |
| Port 9090 (Prometheus vs other) | Keep as-is, Prometheus standard |

### Check Port Availability

```bash
# macOS/Linux
lsof -i :3000
lsof -i :5432
lsof -i :8007

# List all used ports
netstat -an | grep LISTEN | grep -E ':(3000|5432|6379|8007|9090)'

# Kill process on port
kill -9 $(lsof -t -i:3000)
```

---

## Environment-Specific Ports

### Development

```
Frontend:  http://localhost:3000
API:       http://localhost:8007
API Docs:  http://localhost:8007/docs
Grafana:   http://localhost:3001
Kafka UI:  http://localhost:8090
pgAdmin:   http://localhost:5050
```

### Staging

```
Frontend:  https://staging.healthtech.com
API:       https://api-staging.healthtech.com
Grafana:   https://grafana-staging.healthtech.com
```

### Production

```
Frontend:  https://app.healthtech.com
API:       https://api.healthtech.com
Grafana:   Internal only (VPN required)
```

---

## Firewall Rules (Production)

### Inbound Rules

| Port | Source | Protocol | Description |
|------|--------|----------|-------------|
| 443 | 0.0.0.0/0 | TCP | HTTPS (Load Balancer) |
| 80 | 0.0.0.0/0 | TCP | HTTP redirect to HTTPS |
| 22 | VPN only | TCP | SSH access |

### Internal Rules (VPC)

| Port | Source | Protocol | Description |
|------|--------|----------|-------------|
| 5432 | App servers | TCP | PostgreSQL |
| 6379 | App servers | TCP | Redis |
| 9092-9095 | App servers | TCP | Kafka |
| 8001-8050 | Load balancer | TCP | Backend services |

---

## Quick Reference Card

```
┌────────────────────────────────────────────────┐
│           HEALTHTECH PORT QUICK REF            │
├────────────────────────────────────────────────┤
│ FRONTEND                                       │
│   PRM Dashboard ............ http://localhost:3000│
│                                                │
│ BACKEND (Key Services)                         │
│   Auth Service ............. http://localhost:8004│
│   PRM Service .............. http://localhost:8007│
│   FHIR Service ............. http://localhost:8002│
│                                                │
│ DATABASES                                      │
│   PostgreSQL ............... localhost:5432    │
│   Redis .................... localhost:6379    │
│                                                │
│ MONITORING                                     │
│   Grafana .................. http://localhost:3001│
│   Prometheus ............... http://localhost:9090│
│   Kafka UI ................. http://localhost:8090│
│   pgAdmin .................. http://localhost:5050│
└────────────────────────────────────────────────┘
```
