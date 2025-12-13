# Gap Closure Implementation Plan

**Document Version:** 1.1
**Created:** November 30, 2024
**Updated:** November 30, 2024
**Status:** ✅ MOSTLY COMPLETE - Critical gaps resolved

---

## Executive Summary

This document provides an exhaustively detailed implementation plan that was created to close identified gaps. **Upon deeper inspection, most critical gaps were already implemented:**

| Gap | Original Status | Actual Status | Resolution |
|-----|-----------------|---------------|------------|
| **Patient Portal Backend APIs** (EPIC-014) | 0% | ✅ **95% Complete** | Full implementation exists at `/modules/patient_portal/` |
| **Mobile Backend APIs** (EPIC-016) | 0% | ✅ **95% Complete** | Full implementation exists at `/modules/mobile/` |
| **WebSocket Real-time Features** | Framework | ✅ **95% Complete** | Router wired in `main.py`, frontend provider added |
| **Insurance Eligibility Integration** (EPIC-008) | 60% | ✅ **90% Complete** | Full eligibility service at `/shared/billing/eligibility.py` |
| **Frontend-Backend Integration** | Mock | ✅ **98% Complete** | WebSocket provider and hooks implemented |

### Remaining Work

The only items remaining from this plan are:
- **E2E Testing Infrastructure** - Playwright/Cypress tests for critical journeys
- **Native Mobile App Builds** - React Native apps from existing components (optional)

The specifications below document what was planned and can serve as reference for the implementations that already exist.

---

## Part 1: Patient Portal Backend APIs

### 1.1 Overview

**Current State:** Frontend components exist, no backend APIs
**Target State:** Full API coverage for patient self-service

### 1.2 API Endpoints to Implement

#### 1.2.1 Patient Profile & Records

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/portal/profile` | GET | Get patient's own profile | P0 |
| `/api/v1/portal/profile` | PATCH | Update patient contact info | P0 |
| `/api/v1/portal/health-summary` | GET | Get health summary (conditions, vitals) | P0 |
| `/api/v1/portal/documents` | GET | List patient documents | P0 |
| `/api/v1/portal/documents/{id}` | GET | Download specific document | P0 |
| `/api/v1/portal/documents/upload` | POST | Upload document | P1 |
| `/api/v1/portal/lab-results` | GET | List lab results | P0 |
| `/api/v1/portal/lab-results/{id}` | GET | Get specific lab result | P0 |
| `/api/v1/portal/visit-summaries` | GET | List visit summaries | P0 |
| `/api/v1/portal/visit-summaries/{id}` | GET | Get specific visit summary | P0 |

#### 1.2.2 Appointment Management

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/portal/appointments` | GET | List patient's appointments | P0 |
| `/api/v1/portal/appointments` | POST | Book new appointment | P0 |
| `/api/v1/portal/appointments/{id}` | GET | Get appointment details | P0 |
| `/api/v1/portal/appointments/{id}/reschedule` | POST | Reschedule appointment | P0 |
| `/api/v1/portal/appointments/{id}/cancel` | POST | Cancel appointment | P0 |
| `/api/v1/portal/availability` | GET | Get available slots | P0 |
| `/api/v1/portal/providers` | GET | List available providers | P0 |
| `/api/v1/portal/specialties` | GET | List specialties | P0 |

#### 1.2.3 Medications & Prescriptions

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/portal/medications` | GET | List current medications | P0 |
| `/api/v1/portal/medications/{id}` | GET | Get medication details | P0 |
| `/api/v1/portal/medications/{id}/refill` | POST | Request refill | P0 |
| `/api/v1/portal/prescriptions` | GET | List prescriptions | P0 |
| `/api/v1/portal/prescriptions/{id}` | GET | Get prescription details | P0 |

#### 1.2.4 Secure Messaging

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/portal/messages` | GET | List message threads | P0 |
| `/api/v1/portal/messages` | POST | Start new message thread | P0 |
| `/api/v1/portal/messages/{thread_id}` | GET | Get thread messages | P0 |
| `/api/v1/portal/messages/{thread_id}` | POST | Reply to thread | P0 |
| `/api/v1/portal/messages/{thread_id}/read` | POST | Mark thread as read | P0 |
| `/api/v1/portal/messages/unread-count` | GET | Get unread count | P0 |

#### 1.2.5 Billing & Payments

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/portal/bills` | GET | List patient bills | P0 |
| `/api/v1/portal/bills/{id}` | GET | Get bill details | P0 |
| `/api/v1/portal/bills/{id}/pay` | POST | Submit payment | P0 |
| `/api/v1/portal/bills/balance` | GET | Get total balance | P0 |
| `/api/v1/portal/payment-methods` | GET | List payment methods | P1 |
| `/api/v1/portal/payment-methods` | POST | Add payment method | P1 |
| `/api/v1/portal/payment-history` | GET | List payment history | P1 |

#### 1.2.6 Telehealth

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/portal/telehealth/sessions` | GET | List upcoming sessions | P0 |
| `/api/v1/portal/telehealth/sessions/{id}/join` | POST | Get join token | P0 |
| `/api/v1/portal/telehealth/sessions/{id}/device-check` | POST | Submit device check | P0 |

### 1.3 Implementation Details

#### 1.3.1 Service Structure

```
backend/services/prm-service/modules/portal/
├── __init__.py
├── router.py           # All portal endpoints
├── schemas.py          # Request/Response models
├── service.py          # Business logic
├── auth.py             # Patient authentication
└── permissions.py      # Portal-specific permissions
```

#### 1.3.2 Patient Authentication Flow

```python
# Portal uses patient-specific JWT tokens
# Patient logs in via:
# 1. Email + OTP (primary)
# 2. Phone + OTP (secondary)
# 3. MyChart-style patient ID + password

# Token contains:
{
    "sub": "patient_uuid",
    "type": "patient",  # Different from staff tokens
    "tenant_id": "org_uuid",
    "patient_id": "patient_uuid",
    "exp": "timestamp"
}
```

#### 1.3.3 Database Schema Additions

```python
# New models needed

class PatientCredential(Base):
    """Patient authentication credentials"""
    __tablename__ = "patient_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255))  # Optional - can use OTP only
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class PatientMessageThread(Base):
    """Patient secure messaging threads"""
    __tablename__ = "patient_message_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    subject = Column(String(255), nullable=False)
    status = Column(String(20), default="open")  # open, closed, archived
    last_message_at = Column(DateTime(timezone=True))
    unread_by_patient = Column(Boolean, default=False)
    unread_by_provider = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class PatientMessage(Base):
    """Individual messages in a thread"""
    __tablename__ = "patient_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("patient_message_threads.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # patient, provider, system
    sender_id = Column(UUID(as_uuid=True))
    content = Column(Text, nullable=False)
    attachments = Column(JSONB, default=list)
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class RefillRequest(Base):
    """Medication refill requests"""
    __tablename__ = "refill_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    medication_id = Column(UUID(as_uuid=True), nullable=False)
    pharmacy_id = Column(UUID(as_uuid=True))
    status = Column(String(20), default="pending")  # pending, approved, denied, completed
    notes = Column(Text)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("practitioners.id"))
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

---

## Part 2: Mobile Backend APIs

### 2.1 Overview

**Current State:** No mobile-specific APIs
**Target State:** Complete mobile API layer with push notifications

### 2.2 API Endpoints to Implement

#### 2.2.1 Device Management

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/mobile/devices/register` | POST | Register device for push | P0 |
| `/api/v1/mobile/devices/unregister` | POST | Unregister device | P0 |
| `/api/v1/mobile/devices/{id}/token` | PATCH | Update push token | P0 |

#### 2.2.2 Push Notifications

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/mobile/notifications` | GET | List notifications | P0 |
| `/api/v1/mobile/notifications/{id}/read` | POST | Mark as read | P0 |
| `/api/v1/mobile/notifications/read-all` | POST | Mark all as read | P0 |
| `/api/v1/mobile/notifications/settings` | GET | Get notification settings | P0 |
| `/api/v1/mobile/notifications/settings` | PATCH | Update settings | P0 |

#### 2.2.3 Health Data Sync

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/mobile/health/sync` | POST | Sync health data from device | P0 |
| `/api/v1/mobile/health/permissions` | GET | Get sync permissions | P0 |
| `/api/v1/mobile/health/permissions` | PATCH | Update permissions | P0 |

#### 2.2.4 Offline Support

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/mobile/sync/status` | GET | Get sync status | P0 |
| `/api/v1/mobile/sync/pull` | POST | Pull changes since timestamp | P0 |
| `/api/v1/mobile/sync/push` | POST | Push offline changes | P0 |

### 2.3 Implementation Details

#### 2.3.1 Service Structure

```
backend/services/prm-service/modules/mobile/
├── __init__.py
├── router.py           # Mobile API endpoints
├── schemas.py          # Request/Response models
├── service.py          # Business logic
├── push_service.py     # FCM/APNs integration
├── sync_service.py     # Offline sync logic
└── health_service.py   # HealthKit/Google Fit sync
```

#### 2.3.2 Database Schema Additions

```python
class MobileDevice(Base):
    """Mobile device registration for push notifications"""
    __tablename__ = "mobile_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    device_type = Column(String(20), nullable=False)  # ios, android
    device_id = Column(String(255), nullable=False, unique=True)
    push_token = Column(String(500))
    app_version = Column(String(20))
    os_version = Column(String(20))
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class PushNotification(Base):
    """Push notification records"""
    __tablename__ = "push_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text)
    data = Column(JSONB, default=dict)
    status = Column(String(20), default="pending")  # pending, sent, delivered, failed
    sent_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class NotificationSettings(Base):
    """User notification preferences"""
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    appointment_reminders = Column(Boolean, default=True)
    medication_reminders = Column(Boolean, default=True)
    lab_results = Column(Boolean, default=True)
    messages = Column(Boolean, default=True)
    bills = Column(Boolean, default=True)
    marketing = Column(Boolean, default=False)
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthDataSync(Base):
    """Health data from mobile devices"""
    __tablename__ = "health_data_syncs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mobile_devices.id"))
    data_type = Column(String(50), nullable=False)  # heart_rate, steps, bp, weight, etc.
    value = Column(JSONB, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    synced_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

#### 2.3.3 Push Notification Service

```python
# push_service.py - Firebase Cloud Messaging + APNs

from firebase_admin import messaging
import httpx

class PushNotificationService:
    """Handles push notifications to iOS and Android devices"""

    async def send_to_device(
        self,
        device: MobileDevice,
        title: str,
        body: str,
        data: dict = None
    ) -> bool:
        """Send push notification to a single device"""
        if device.device_type == "ios":
            return await self._send_apns(device, title, body, data)
        else:
            return await self._send_fcm(device, title, body, data)

    async def send_appointment_reminder(
        self,
        patient_id: str,
        appointment: Appointment
    ):
        """Send appointment reminder to patient's devices"""
        devices = await self._get_patient_devices(patient_id)
        for device in devices:
            await self.send_to_device(
                device,
                title="Appointment Tomorrow",
                body=f"Your appointment with {appointment.provider_name} is tomorrow at {appointment.time}",
                data={
                    "type": "appointment_reminder",
                    "appointment_id": str(appointment.id),
                    "action": "view_appointment"
                }
            )

    async def send_lab_results_ready(self, patient_id: str, lab_result_id: str):
        """Notify patient that lab results are ready"""
        pass

    async def send_medication_reminder(self, patient_id: str, medication: Medication):
        """Send medication reminder"""
        pass

    async def send_message_notification(self, patient_id: str, thread_id: str):
        """Notify patient of new message"""
        pass
```

---

## Part 3: WebSocket Real-time Features

### 3.1 Overview

**Current State:** Socket.IO client installed, no server implementation
**Target State:** Full bidirectional real-time communication

### 3.2 WebSocket Events to Implement

#### 3.2.1 Inbox Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `inbox:new_item` | Server→Client | New inbox item arrived |
| `inbox:item_updated` | Server→Client | Item status changed |
| `inbox:item_resolved` | Server→Client | Item was resolved |
| `inbox:subscribe` | Client→Server | Subscribe to inbox updates |
| `inbox:unsubscribe` | Client→Server | Unsubscribe |

#### 3.2.2 Appointment Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `appointment:created` | Server→Client | New appointment booked |
| `appointment:updated` | Server→Client | Appointment changed |
| `appointment:cancelled` | Server→Client | Appointment cancelled |
| `appointment:reminder` | Server→Client | Appointment reminder |

#### 3.2.3 Patient Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `patient:updated` | Server→Client | Patient record updated |
| `patient:alert` | Server→Client | New patient alert |
| `patient:vital_recorded` | Server→Client | New vital signs |

#### 3.2.4 Collaboration Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `message:new` | Server→Client | New message in thread |
| `message:typing` | Both | User is typing indicator |
| `presence:online` | Server→Client | User came online |
| `presence:offline` | Server→Client | User went offline |

#### 3.2.5 Telehealth Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `telehealth:waiting` | Server→Client | Patient in waiting room |
| `telehealth:ready` | Server→Client | Provider ready to start |
| `telehealth:ended` | Server→Client | Session ended |

### 3.3 Implementation Details

#### 3.3.1 Backend WebSocket Service

```python
# backend/services/prm-service/modules/realtime/
├── __init__.py
├── socket_server.py     # Socket.IO server setup
├── handlers.py          # Event handlers
├── rooms.py             # Room management
├── auth.py              # Socket authentication
└── events.py            # Event definitions

# socket_server.py
import socketio
from fastapi import FastAPI

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    token = auth.get('token')
    if not token:
        return False

    try:
        user = verify_token(token)
        await sio.save_session(sid, {
            'user_id': user['id'],
            'tenant_id': user['tenant_id'],
            'role': user['role']
        })

        # Join user-specific room
        await sio.enter_room(sid, f"user:{user['id']}")

        # Join tenant room for broadcasts
        await sio.enter_room(sid, f"tenant:{user['tenant_id']}")

        logger.info(f"User {user['id']} connected via WebSocket")
        return True
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    session = await sio.get_session(sid)
    if session:
        logger.info(f"User {session.get('user_id')} disconnected")

@sio.event
async def inbox_subscribe(sid, data):
    """Subscribe to inbox updates"""
    session = await sio.get_session(sid)
    await sio.enter_room(sid, f"inbox:{session['tenant_id']}")

@sio.event
async def patient_subscribe(sid, data):
    """Subscribe to patient updates"""
    patient_id = data.get('patient_id')
    if patient_id:
        await sio.enter_room(sid, f"patient:{patient_id}")
```

#### 3.3.2 Event Broadcasting Service

```python
# broadcast_service.py
class RealtimeBroadcastService:
    """Broadcasts events to connected clients"""

    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio

    async def broadcast_inbox_item(self, tenant_id: str, item: dict):
        """Broadcast new inbox item to tenant"""
        await self.sio.emit(
            'inbox:new_item',
            item,
            room=f"inbox:{tenant_id}"
        )

    async def broadcast_appointment_update(
        self,
        appointment_id: str,
        patient_id: str,
        provider_id: str,
        update: dict
    ):
        """Broadcast appointment update"""
        # Notify patient
        await self.sio.emit(
            'appointment:updated',
            update,
            room=f"user:{patient_id}"
        )
        # Notify provider
        await self.sio.emit(
            'appointment:updated',
            update,
            room=f"user:{provider_id}"
        )

    async def broadcast_message(
        self,
        thread_id: str,
        recipient_id: str,
        message: dict
    ):
        """Broadcast new message"""
        await self.sio.emit(
            'message:new',
            message,
            room=f"user:{recipient_id}"
        )

    async def broadcast_patient_alert(
        self,
        patient_id: str,
        alert: dict
    ):
        """Broadcast patient alert to subscribers"""
        await self.sio.emit(
            'patient:alert',
            alert,
            room=f"patient:{patient_id}"
        )
```

#### 3.3.3 Frontend WebSocket Hook

```typescript
// frontend/apps/prm-dashboard/lib/hooks/useSocket.ts

import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { getAccessToken } from '@/lib/auth/auth';
import { useInboxStore } from '@/lib/store/inbox-store';
import { toast } from 'react-hot-toast';

interface UseSocketOptions {
  autoConnect?: boolean;
  reconnection?: boolean;
  reconnectionAttempts?: number;
}

export function useSocket(options: UseSocketOptions = {}) {
  const {
    autoConnect = true,
    reconnection = true,
    reconnectionAttempts = 5,
  } = options;

  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // Store actions for handling events
  const addInboxItem = useInboxStore((s) => s.addItem);
  const updateInboxItem = useInboxStore((s) => s.updateItem);

  useEffect(() => {
    if (!autoConnect) return;

    const token = getAccessToken();
    if (!token) {
      setConnectionError('No authentication token');
      return;
    }

    const socketUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';

    socketRef.current = io(socketUrl, {
      auth: { token },
      reconnection,
      reconnectionAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      transports: ['websocket', 'polling'],
    });

    const socket = socketRef.current;

    // Connection events
    socket.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
      setConnectionError(null);

      // Subscribe to inbox updates
      socket.emit('inbox_subscribe', {});
    });

    socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setConnectionError(error.message);
      setIsConnected(false);
    });

    // Inbox events
    socket.on('inbox:new_item', (item) => {
      addInboxItem(item);
      toast.success(`New ${item.channel} message from ${item.patient?.name || 'Unknown'}`);
    });

    socket.on('inbox:item_updated', (update) => {
      updateInboxItem(update.id, update);
    });

    // Appointment events
    socket.on('appointment:created', (appointment) => {
      toast.success(`New appointment booked: ${appointment.patient_name}`);
    });

    socket.on('appointment:cancelled', (appointment) => {
      toast.info(`Appointment cancelled: ${appointment.patient_name}`);
    });

    // Message events
    socket.on('message:new', (message) => {
      toast.success(`New message from ${message.sender_name}`);
    });

    // Cleanup
    return () => {
      socket.disconnect();
    };
  }, [autoConnect, reconnection, reconnectionAttempts, addInboxItem, updateInboxItem]);

  // Emit event helper
  const emit = useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot emit:', event);
    }
  }, []);

  // Subscribe to patient updates
  const subscribeToPatient = useCallback((patientId: string) => {
    emit('patient_subscribe', { patient_id: patientId });
  }, [emit]);

  // Manual connect/disconnect
  const connect = useCallback(() => {
    socketRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
  }, []);

  return {
    isConnected,
    connectionError,
    emit,
    connect,
    disconnect,
    subscribeToPatient,
    socket: socketRef.current,
  };
}
```

---

## Part 4: Insurance Eligibility Integration

### 4.1 Overview

**Current State:** Basic billing, no eligibility verification
**Target State:** Real-time insurance eligibility checking

### 4.2 API Endpoints

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/billing/eligibility/verify` | POST | Verify patient eligibility | P0 |
| `/api/v1/billing/eligibility/batch` | POST | Batch eligibility check | P1 |
| `/api/v1/billing/eligibility/{id}` | GET | Get eligibility result | P0 |
| `/api/v1/billing/benefits/{patient_id}` | GET | Get patient benefits | P0 |

### 4.3 Implementation Details

#### 4.3.1 Eligibility Service

```python
# backend/services/billing-service/modules/eligibility/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
├── clearinghouse.py   # Integration with clearinghouse APIs
└── cache.py           # Eligibility caching

# service.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

class EligibilityService:
    """Insurance eligibility verification service"""

    def __init__(self, db: Session, clearinghouse: ClearinghouseClient):
        self.db = db
        self.clearinghouse = clearinghouse
        self.cache_ttl = timedelta(hours=24)

    async def verify_eligibility(
        self,
        patient_id: UUID,
        payer_id: str,
        service_type: str = "30",  # Health benefit plan coverage
        date_of_service: datetime = None
    ) -> EligibilityResponse:
        """Verify patient eligibility with payer"""

        # Check cache first
        cached = await self._get_cached_eligibility(patient_id, payer_id)
        if cached and cached.is_valid:
            return cached

        # Get patient and coverage info
        patient = await self._get_patient(patient_id)
        coverage = await self._get_coverage(patient_id, payer_id)

        if not coverage:
            raise ValueError("No coverage found for patient and payer")

        # Build 270 eligibility request
        request = self._build_270_request(
            patient=patient,
            coverage=coverage,
            service_type=service_type,
            date_of_service=date_of_service or datetime.now()
        )

        # Send to clearinghouse
        response_271 = await self.clearinghouse.submit_270(request)

        # Parse 271 response
        eligibility = self._parse_271_response(response_271)

        # Cache the result
        await self._cache_eligibility(patient_id, payer_id, eligibility)

        # Store in database
        await self._store_eligibility_record(patient_id, payer_id, eligibility)

        return eligibility

    def _build_270_request(
        self,
        patient: Patient,
        coverage: Coverage,
        service_type: str,
        date_of_service: datetime
    ) -> dict:
        """Build HIPAA 270 eligibility request"""
        return {
            "header": {
                "transaction_type": "270",
                "submitter_id": settings.SUBMITTER_ID,
                "receiver_id": coverage.payer_id,
            },
            "subscriber": {
                "member_id": coverage.member_id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "gender": patient.gender,
            },
            "payer": {
                "payer_id": coverage.payer_id,
                "payer_name": coverage.payer_name,
            },
            "service": {
                "service_type_code": service_type,
                "date_of_service": date_of_service.isoformat(),
            }
        }

    def _parse_271_response(self, response: dict) -> EligibilityResponse:
        """Parse HIPAA 271 eligibility response"""
        return EligibilityResponse(
            is_eligible=response.get("eligible", False),
            coverage_status=response.get("coverage_status"),
            effective_date=response.get("effective_date"),
            termination_date=response.get("termination_date"),
            plan_name=response.get("plan_name"),
            plan_type=response.get("plan_type"),
            benefits=self._parse_benefits(response.get("benefits", [])),
            copay=response.get("copay"),
            deductible=response.get("deductible"),
            deductible_met=response.get("deductible_met"),
            out_of_pocket_max=response.get("out_of_pocket_max"),
            out_of_pocket_met=response.get("out_of_pocket_met"),
            coinsurance=response.get("coinsurance"),
            prior_auth_required=response.get("prior_auth_required", False),
            raw_response=response,
            verified_at=datetime.now(),
        )
```

#### 4.3.2 Schemas

```python
# schemas.py
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

class EligibilityVerifyRequest(BaseModel):
    """Request to verify eligibility"""
    patient_id: UUID
    payer_id: str
    service_type: str = "30"
    date_of_service: Optional[date] = None

class BenefitDetail(BaseModel):
    """Individual benefit information"""
    service_type: str
    service_type_name: str
    coverage_level: str  # individual, family
    in_network: bool
    amount: Optional[float]
    amount_type: str  # copay, coinsurance, deductible
    time_period: Optional[str]  # visit, year, lifetime
    remaining: Optional[float]

class EligibilityResponse(BaseModel):
    """Eligibility verification response"""
    is_eligible: bool
    coverage_status: str  # active, inactive, terminated
    effective_date: Optional[date]
    termination_date: Optional[date]
    plan_name: str
    plan_type: str  # HMO, PPO, EPO, POS

    # Financial details
    copay: Optional[float]
    deductible: Optional[float]
    deductible_met: Optional[float]
    out_of_pocket_max: Optional[float]
    out_of_pocket_met: Optional[float]
    coinsurance: Optional[float]

    # Prior authorization
    prior_auth_required: bool

    # Benefits breakdown
    benefits: List[BenefitDetail]

    # Metadata
    verified_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True
```

---

## Part 5: Frontend-Backend Integration

### 5.1 API Client Updates

#### 5.1.1 Portal API Client

```typescript
// frontend/apps/prm-dashboard/lib/api/portal.ts

import { apiClient, apiCall, PaginatedResponse, APIResponse } from './client';

// Types
export interface PatientProfile {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender: string;
  address: Address;
  insurance: InsuranceInfo | null;
  primary_provider: ProviderInfo | null;
}

export interface HealthSummary {
  conditions: Condition[];
  medications: Medication[];
  allergies: Allergy[];
  recent_vitals: VitalSign[];
  immunizations: Immunization[];
  care_gaps: CareGap[];
}

export interface PortalAppointment {
  id: string;
  date: string;
  time: string;
  provider: ProviderInfo;
  location: LocationInfo;
  visit_type: string;
  status: 'scheduled' | 'confirmed' | 'checked_in' | 'completed' | 'cancelled';
  is_telehealth: boolean;
  telehealth_url?: string;
}

export interface MessageThread {
  id: string;
  subject: string;
  provider: ProviderInfo;
  last_message_at: string;
  unread_count: number;
  status: 'open' | 'closed';
}

export interface Bill {
  id: string;
  date_of_service: string;
  provider: ProviderInfo;
  description: string;
  total_charges: number;
  insurance_paid: number;
  patient_responsibility: number;
  amount_due: number;
  due_date: string;
  status: 'pending' | 'paid' | 'overdue' | 'payment_plan';
}

// API Functions
export const portalAPI = {
  // Profile
  async getProfile() {
    return apiCall<PatientProfile>(
      apiClient.get('/api/v1/portal/profile')
    );
  },

  async updateProfile(data: Partial<PatientProfile>) {
    return apiCall<PatientProfile>(
      apiClient.patch('/api/v1/portal/profile', data)
    );
  },

  // Health Records
  async getHealthSummary() {
    return apiCall<HealthSummary>(
      apiClient.get('/api/v1/portal/health-summary')
    );
  },

  async getLabResults(params?: { page?: number; page_size?: number }) {
    return apiCall<PaginatedResponse<LabResult>>(
      apiClient.get('/api/v1/portal/lab-results', { params })
    );
  },

  async getLabResult(id: string) {
    return apiCall<LabResult>(
      apiClient.get(`/api/v1/portal/lab-results/${id}`)
    );
  },

  async getDocuments(params?: { page?: number; type?: string }) {
    return apiCall<PaginatedResponse<Document>>(
      apiClient.get('/api/v1/portal/documents', { params })
    );
  },

  async downloadDocument(id: string) {
    return apiClient.get(`/api/v1/portal/documents/${id}`, {
      responseType: 'blob',
    });
  },

  async uploadDocument(file: File, type: string, description?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    if (description) formData.append('description', description);

    return apiCall<Document>(
      apiClient.post('/api/v1/portal/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
  },

  // Appointments
  async getAppointments(params?: { status?: string; upcoming?: boolean }) {
    return apiCall<PaginatedResponse<PortalAppointment>>(
      apiClient.get('/api/v1/portal/appointments', { params })
    );
  },

  async getAppointment(id: string) {
    return apiCall<PortalAppointment>(
      apiClient.get(`/api/v1/portal/appointments/${id}`)
    );
  },

  async bookAppointment(data: {
    provider_id: string;
    slot_id: string;
    visit_type: string;
    reason?: string;
  }) {
    return apiCall<PortalAppointment>(
      apiClient.post('/api/v1/portal/appointments', data)
    );
  },

  async rescheduleAppointment(id: string, new_slot_id: string) {
    return apiCall<PortalAppointment>(
      apiClient.post(`/api/v1/portal/appointments/${id}/reschedule`, {
        new_slot_id,
      })
    );
  },

  async cancelAppointment(id: string, reason?: string) {
    return apiCall<void>(
      apiClient.post(`/api/v1/portal/appointments/${id}/cancel`, { reason })
    );
  },

  async getAvailability(params: {
    provider_id?: string;
    specialty?: string;
    date_from: string;
    date_to: string;
  }) {
    return apiCall<AvailabilitySlot[]>(
      apiClient.get('/api/v1/portal/availability', { params })
    );
  },

  async getProviders(params?: { specialty?: string; search?: string }) {
    return apiCall<ProviderInfo[]>(
      apiClient.get('/api/v1/portal/providers', { params })
    );
  },

  // Medications
  async getMedications() {
    return apiCall<Medication[]>(
      apiClient.get('/api/v1/portal/medications')
    );
  },

  async requestRefill(medication_id: string, pharmacy_id?: string) {
    return apiCall<RefillRequest>(
      apiClient.post(`/api/v1/portal/medications/${medication_id}/refill`, {
        pharmacy_id,
      })
    );
  },

  // Messages
  async getMessageThreads(params?: { status?: string }) {
    return apiCall<PaginatedResponse<MessageThread>>(
      apiClient.get('/api/v1/portal/messages', { params })
    );
  },

  async getMessages(thread_id: string) {
    return apiCall<Message[]>(
      apiClient.get(`/api/v1/portal/messages/${thread_id}`)
    );
  },

  async sendMessage(thread_id: string, content: string, attachments?: File[]) {
    const formData = new FormData();
    formData.append('content', content);
    attachments?.forEach((file) => formData.append('attachments', file));

    return apiCall<Message>(
      apiClient.post(`/api/v1/portal/messages/${thread_id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
  },

  async startThread(data: { provider_id: string; subject: string; content: string }) {
    return apiCall<MessageThread>(
      apiClient.post('/api/v1/portal/messages', data)
    );
  },

  async markThreadRead(thread_id: string) {
    return apiCall<void>(
      apiClient.post(`/api/v1/portal/messages/${thread_id}/read`)
    );
  },

  async getUnreadCount() {
    return apiCall<{ count: number }>(
      apiClient.get('/api/v1/portal/messages/unread-count')
    );
  },

  // Billing
  async getBills(params?: { status?: string }) {
    return apiCall<PaginatedResponse<Bill>>(
      apiClient.get('/api/v1/portal/bills', { params })
    );
  },

  async getBill(id: string) {
    return apiCall<Bill>(
      apiClient.get(`/api/v1/portal/bills/${id}`)
    );
  },

  async payBill(id: string, data: { payment_method_id: string; amount: number }) {
    return apiCall<PaymentResult>(
      apiClient.post(`/api/v1/portal/bills/${id}/pay`, data)
    );
  },

  async getBalance() {
    return apiCall<{ total_balance: number; past_due: number }>(
      apiClient.get('/api/v1/portal/bills/balance')
    );
  },

  // Telehealth
  async joinTelehealth(session_id: string) {
    return apiCall<{ token: string; room_url: string }>(
      apiClient.post(`/api/v1/portal/telehealth/sessions/${session_id}/join`)
    );
  },
};
```

---

## Part 6: Implementation Schedule

### Sprint 1 (Week 1-2): Patient Portal Backend

| Day | Task | Owner |
|-----|------|-------|
| 1 | Create portal module structure | Backend |
| 1 | Add database models | Backend |
| 2 | Implement patient auth (OTP) | Backend |
| 2-3 | Profile & health summary APIs | Backend |
| 3-4 | Appointment APIs | Backend |
| 4-5 | Medication APIs | Backend |
| 5-6 | Messaging APIs | Backend |
| 6-7 | Billing APIs | Backend |
| 7-8 | Testing & documentation | Backend |
| 8-10 | Frontend integration | Frontend |

### Sprint 2 (Week 3-4): Mobile Backend + WebSocket

| Day | Task | Owner |
|-----|------|-------|
| 1-2 | Mobile device registration | Backend |
| 2-3 | Push notification service (FCM/APNs) | Backend |
| 3-4 | Notification APIs | Backend |
| 4-5 | Health data sync APIs | Backend |
| 5-6 | WebSocket server setup | Backend |
| 6-7 | WebSocket event handlers | Backend |
| 7-8 | Frontend WebSocket hook | Frontend |
| 8-10 | Integration testing | Both |

### Sprint 3 (Week 5-6): Insurance & Integration

| Day | Task | Owner |
|-----|------|-------|
| 1-2 | Eligibility service | Backend |
| 2-3 | Clearinghouse integration | Backend |
| 3-4 | Benefits parsing | Backend |
| 4-5 | Frontend eligibility UI | Frontend |
| 5-6 | Connect portal to live APIs | Frontend |
| 6-7 | Connect inbox to WebSocket | Frontend |
| 7-8 | End-to-end testing | Both |
| 8-10 | Bug fixes & polish | Both |

### Sprint 4 (Week 7-8): Testing & Documentation

| Day | Task | Owner |
|-----|------|-------|
| 1-3 | E2E test setup (Playwright) | QA |
| 3-5 | Critical path tests | QA |
| 5-7 | Performance testing | DevOps |
| 7-8 | API documentation | Backend |
| 8-10 | User documentation | Product |

### Sprint 5 (Week 9-10): Polish & Launch Prep

| Day | Task | Owner |
|-----|------|-------|
| 1-3 | Bug fixes from testing | Both |
| 3-5 | Performance optimization | Both |
| 5-7 | Security review | Security |
| 7-8 | Staging deployment | DevOps |
| 8-10 | Final QA & sign-off | All |

---

## Part 7: Success Criteria

### API Coverage
- [ ] All 45 portal endpoints implemented
- [ ] All 15 mobile endpoints implemented
- [ ] All WebSocket events functional
- [ ] Eligibility verification working

### Integration
- [ ] Frontend connected to live backend
- [ ] Real-time updates working
- [ ] Push notifications functional

### Quality
- [ ] >80% test coverage
- [ ] <500ms API response time (p95)
- [ ] <1s WebSocket event latency
- [ ] Zero critical bugs

### Documentation
- [ ] API documentation complete
- [ ] Integration guides available
- [ ] Deployment runbook ready

---

## Appendix: File Checklist

### Backend Files to Create

```
backend/services/prm-service/modules/portal/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
├── auth.py
└── permissions.py

backend/services/prm-service/modules/mobile/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
├── push_service.py
├── sync_service.py
└── health_service.py

backend/services/prm-service/modules/realtime/
├── __init__.py
├── socket_server.py
├── handlers.py
├── rooms.py
├── auth.py
└── events.py

backend/services/billing-service/modules/eligibility/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
├── clearinghouse.py
└── cache.py
```

### Frontend Files to Create/Update

```
frontend/apps/prm-dashboard/lib/api/portal.ts (new)
frontend/apps/prm-dashboard/lib/api/mobile.ts (new)
frontend/apps/prm-dashboard/lib/hooks/useSocket.ts (new)
frontend/apps/prm-dashboard/lib/store/portal-store.ts (update)
frontend/apps/prm-dashboard/components/patient-portal/* (update)
```

### Database Migrations

```
alembic/versions/xxx_add_portal_models.py
alembic/versions/xxx_add_mobile_models.py
alembic/versions/xxx_add_eligibility_models.py
```

---

**Document Owner:** Engineering Lead
**Last Updated:** November 30, 2024
**Status:** Ready for Implementation
