# API Mapping Document - Part 4

## UX-010: Provider Collaboration Hub
## UX-011: Patient Self-Service Portal
## UX-012: Mobile Applications

---

## 1. Backend API Inventory (Relevant Modules)

### 1.1 Provider Collaboration Module (`/api/v1/prm/collaboration/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/presence` | PUT | Update provider presence status |
| `/presence/{provider_id}` | GET | Get provider online status |
| `/presence/bulk` | POST | Get multiple providers' status |
| `/conversations` | POST | Create conversation thread |
| `/conversations` | GET | List conversations |
| `/conversations/{id}` | GET | Get conversation details |
| `/conversations/{id}/participants` | POST | Add participant |
| `/conversations/{id}/participants/{pid}` | DELETE | Remove participant |
| `/conversations/{id}/messages` | POST | Send message |
| `/conversations/{id}/messages` | GET | Get messages |
| `/messages/{id}/read` | POST | Mark message read |
| `/conversations/{id}/read` | POST | Mark all messages read |
| `/messages/{id}/reactions` | POST | Add reaction |
| `/messages/{id}` | DELETE | Recall message |
| `/consultations` | POST | Request consultation |
| `/consultations` | GET | List consultations |
| `/consultations/{id}` | GET | Get consultation details |
| `/consultations/{id}/accept` | POST | Accept consultation |
| `/consultations/{id}/decline` | POST | Decline consultation |
| `/consultations/{id}/start` | POST | Start consultation |
| `/consultations/{id}/report` | POST | Create consultation report |
| `/consultations/{id}/complete` | POST | Complete consultation |
| `/care-teams` | POST | Create care team |
| `/care-teams` | GET | List care teams |
| `/care-teams/{id}` | GET | Get care team |
| `/care-teams/{id}/members` | POST | Add team member |
| `/care-teams/{id}/tasks` | POST | Create task |
| `/care-teams/{id}/tasks` | GET | List tasks |
| `/tasks/{id}/complete` | POST | Complete task |
| `/handoffs` | POST | Create shift handoff |
| `/handoffs` | GET | List handoffs |
| `/handoffs/{id}` | GET | Get handoff details |
| `/handoffs/{id}/start` | POST | Start handoff |
| `/handoffs/{id}/acknowledge` | POST | Acknowledge handoff |
| `/handoffs/patients/{pid}/sbar` | GET | Generate SBAR |
| `/oncall/schedules` | POST | Create on-call schedule |
| `/oncall/schedules` | GET | List schedules |
| `/oncall/current` | GET | Get current on-call |
| `/oncall/requests` | POST | Create on-call request |
| `/oncall/requests/{id}/acknowledge` | POST | Acknowledge request |
| `/alerts` | POST | Create clinical alert |
| `/alerts` | GET | List alerts |
| `/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/alerts/{id}/resolve` | POST | Resolve alert |

### 1.2 Patient Portal Module (`/api/v1/prm/portal/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/register` | POST | Patient registration |
| `/auth/login` | POST | Patient login |
| `/auth/refresh` | POST | Refresh token |
| `/auth/logout` | POST | Logout |
| `/auth/password/reset` | POST | Reset password |
| `/auth/mfa/setup` | POST | Setup MFA |
| `/auth/mfa/verify` | POST | Verify MFA |
| `/profile` | GET | Get patient profile |
| `/profile` | PATCH | Update profile |
| `/preferences` | GET | Get preferences |
| `/preferences` | PATCH | Update preferences |
| `/health-records` | GET | Get health records |
| `/health-records/lab-results` | GET | Get lab results |
| `/health-records/summary` | GET | Get health summary |
| `/health-records/share` | POST | Share records |
| `/messages` | GET | Get message threads |
| `/messages` | POST | Create message thread |
| `/messages/{thread_id}` | GET | Get thread messages |
| `/messages/{thread_id}/reply` | POST | Reply to thread |
| `/notifications` | GET | Get notifications |
| `/notifications/read` | POST | Mark notifications read |
| `/billing/summary` | GET | Get billing summary |
| `/billing/payment-methods` | GET | Get payment methods |
| `/billing/payment-methods` | POST | Add payment method |
| `/billing/payments` | POST | Make payment |
| `/billing/payments/history` | GET | Get payment history |
| `/billing/payment-plans` | GET | Get payment plans |
| `/billing/payment-plans` | POST | Create payment plan |
| `/prescriptions` | GET | Get prescriptions |
| `/prescriptions/refill` | POST | Request refill |
| `/prescriptions/refills` | GET | Get refill requests |
| `/proxy-accounts` | GET | Get proxy accounts |
| `/proxy-access` | POST | Grant proxy access |
| `/sessions` | GET | Get active sessions |
| `/sessions/revoke` | POST | Revoke sessions |

### 1.3 Mobile Module (`/api/v1/prm/mobile/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/devices/register` | POST | Register device |
| `/devices/{id}` | PUT | Update device |
| `/devices/{id}` | GET | Get device |
| `/devices` | GET | List user devices |
| `/devices/{id}/token` | PUT | Update push token |
| `/devices/{id}/deactivate` | POST | Deactivate device |
| `/devices/{id}/revoke` | POST | Revoke device |
| `/auth/session` | POST | Create mobile session |
| `/auth/refresh` | POST | Refresh session |
| `/auth/biometric` | POST | Biometric auth |
| `/auth/biometric/challenge` | POST | Get biometric challenge |
| `/auth/biometric/enable` | POST | Enable biometric |
| `/auth/biometric/disable` | POST | Disable biometric |
| `/auth/logout` | POST | Mobile logout |
| `/auth/logout-all` | POST | Logout all devices |
| `/auth/sessions` | GET | Get active sessions |
| `/notifications/send` | POST | Send notification |
| `/notifications/send-bulk` | POST | Send bulk notifications |
| `/notifications` | GET | Get user notifications |
| `/notifications/{id}/read` | POST | Mark notification read |
| `/notifications/preferences` | GET | Get notification prefs |
| `/notifications/preferences` | PUT | Update notification prefs |
| `/sync/pull` | POST | Pull sync changes |
| `/sync/push` | POST | Push local changes |
| `/sync/conflicts/{id}/resolve` | POST | Resolve sync conflict |
| `/sync/status` | GET | Get sync status |
| `/wearables/connect` | POST | Connect wearable |
| `/wearables/{id}` | PUT | Update wearable |
| `/wearables/{id}/disconnect` | POST | Disconnect wearable |
| `/wearables` | GET | List wearables |
| `/wearables/{id}/sync` | POST | Sync wearable data |
| `/health-metrics` | POST | Record health metric |
| `/health-metrics/bulk` | POST | Record bulk metrics |
| `/health-metrics` | GET | Get health metrics |
| `/health-metrics/summary` | GET | Get metric summary |
| `/health-metrics/trends` | GET | Get metric trends |
| `/health-goals` | POST | Create health goal |
| `/health-goals` | GET | Get health goals |
| `/health-goals/{id}/progress` | GET | Get goal progress |

---

## 2. UX-010: Provider Collaboration Hub - API Mapping

### 2.1 UI Layout: Messaging Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MESSAGES                                                  [+ New Message]   │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ CONVERSATIONS                     │ {recipient_name}                        │
│                                   │ {status_icon} {status}                  │
│ 🔍 Search conversations...       │                                         │
│                                   │ ─────────────────────────────────────── │
│ ┌─────────────────────────────┐  │                                         │
│ │ 👩‍⚕️ {name}        {status}   │  │ {date}                                  │
│ │    "{preview}..."           │  │                                         │
│ │    {time_ago}               │  │ 👤 Re: {patient_name} (MRN: {mrn})      │
│ └─────────────────────────────┘  │                                         │
│                                   │ {sender}: {message_content}             │
│ 📋 Direct Messages               │                                {time} ✓ │
│ 👥 Group Chats                   │                                         │
│ 🏥 Department Channels           │ ─────────────────────────────────────── │
│                                   │ ┌─────────────────────────────────────┐ │
│                                   │ │ 📎 Attach │ 👤 Patient │ Type...   │ │
│                                   │ └─────────────────────────────────────┘ │
│                                   │                                         │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

### 2.2 API Mapping for Provider Collaboration

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Presence Status | `/collaboration/presence` | PUT | Update own status |
| Presence Indicator | `/collaboration/presence/{id}` | GET | Get provider status |
| Bulk Presence | `/collaboration/presence/bulk` | POST | Get team status |
| Conversation List | `/collaboration/conversations` | GET | Filter by type |
| Create Conversation | `/collaboration/conversations` | POST | New thread |
| Get Messages | `/collaboration/conversations/{id}/messages` | GET | Paginated |
| Send Message | `/collaboration/conversations/{id}/messages` | POST | Send new |
| Mark Read | `/collaboration/conversations/{id}/read` | POST | Mark thread read |
| Add Participant | `/collaboration/conversations/{id}/participants` | POST | Add to group |
| Link Patient | `/collaboration/conversations` | POST | patient_id in body |

### 2.3 Consultation Request API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Create Consultation | `/collaboration/consultations` | POST | New consult request |
| List Consultations | `/collaboration/consultations` | GET | Filter by role, status |
| Get Consultation | `/collaboration/consultations/{id}` | GET | Full details |
| Accept Consultation | `/collaboration/consultations/{id}/accept` | POST | Accept request |
| Decline Consultation | `/collaboration/consultations/{id}/decline` | POST | Decline with reason |
| Start Consultation | `/collaboration/consultations/{id}/start` | POST | Begin consult |
| Create Report | `/collaboration/consultations/{id}/report` | POST | Consultation report |
| Complete Consultation | `/collaboration/consultations/{id}/complete` | POST | Mark complete |

### 2.4 SBAR Handoff API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Create Handoff | `/collaboration/handoffs` | POST | New handoff session |
| List Handoffs | `/collaboration/handoffs` | GET | Filter by role, date |
| Get Handoff | `/collaboration/handoffs/{id}` | GET | Full details |
| Start Handoff | `/collaboration/handoffs/{id}/start` | POST | Begin handoff |
| Update Patient SBAR | `/collaboration/handoffs/patients/{id}` | PUT | Update SBAR data |
| Acknowledge Handoff | `/collaboration/handoffs/{id}/acknowledge` | POST | Receive handoff |
| Generate SBAR | `/collaboration/handoffs/patients/{pid}/sbar` | GET | AI-generated SBAR |

### 2.5 On-Call Schedule API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| View Schedule | `/collaboration/oncall/schedules` | GET | Filter by specialty |
| Create Schedule | `/collaboration/oncall/schedules` | POST | Add coverage |
| Update Schedule | `/collaboration/oncall/schedules/{id}` | PUT | Modify schedule |
| Get Current On-Call | `/collaboration/oncall/current` | GET | By specialty |
| Create On-Call Request | `/collaboration/oncall/requests` | POST | Request on-call |
| Acknowledge Request | `/collaboration/oncall/requests/{id}/acknowledge` | POST | Accept request |
| Complete Request | `/collaboration/oncall/requests/{id}/complete` | POST | Resolve request |

### 2.6 TypeScript Implementation Pattern

```typescript
// Real-time Messaging with WebSocket
const useProviderMessaging = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  // WebSocket for real-time messages
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/collaboration/messages`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_message') {
        if (data.conversation_id === activeConversation) {
          setMessages(prev => [...prev, data.message]);
        }
        // Update conversation preview
        setConversations(prev =>
          prev.map(c =>
            c.id === data.conversation_id
              ? { ...c, last_message: data.message, unread_count: c.unread_count + 1 }
              : c
          )
        );
      } else if (data.type === 'presence_update') {
        updatePresenceStatus(data.provider_id, data.status);
      }
    };

    return () => ws.close();
  }, [activeConversation]);

  // Send message
  const sendMessage = async (content: string, patientId?: string) => {
    const response = await api.post(
      `/collaboration/conversations/${activeConversation}/messages`,
      {
        content,
        patient_id: patientId,
        message_type: 'text'
      }
    );
    return response;
  };

  // Create consultation request
  const requestConsultation = async (data: ConsultationCreate) => {
    return await api.post('/collaboration/consultations', data);
  };

  return {
    conversations,
    messages,
    sendMessage,
    requestConsultation,
    setActiveConversation
  };
};

// SBAR Handoff Component
interface SBARHandoffFormProps {
  patients: Patient[];
  toProvider: Practitioner;
  onSubmit: (handoff: HandoffCreate) => void;
}

const SBARHandoffForm: React.FC<SBARHandoffFormProps> = ({ patients, toProvider, onSubmit }) => {
  const [patientSBAR, setPatientSBAR] = useState<Record<string, SBARData>>({});

  // Auto-generate SBAR for each patient
  useEffect(() => {
    const generateSBAR = async () => {
      for (const patient of patients) {
        const sbar = await api.get(`/collaboration/handoffs/patients/${patient.id}/sbar`);
        setPatientSBAR(prev => ({ ...prev, [patient.id]: sbar }));
      }
    };
    generateSBAR();
  }, [patients]);

  const submitHandoff = async () => {
    const handoff = await api.post('/collaboration/handoffs', {
      to_provider_id: toProvider.id,
      patients: patients.map(p => ({
        patient_id: p.id,
        situation: patientSBAR[p.id].situation,
        background: patientSBAR[p.id].background,
        assessment: patientSBAR[p.id].assessment,
        recommendation: patientSBAR[p.id].recommendation
      }))
    });
    onSubmit(handoff);
  };

  return (
    <div className="sbar-handoff-form">
      {patients.map(patient => (
        <SBARPatientCard
          key={patient.id}
          patient={patient}
          sbar={patientSBAR[patient.id]}
          onEdit={(field, value) => {
            setPatientSBAR(prev => ({
              ...prev,
              [patient.id]: { ...prev[patient.id], [field]: value }
            }));
          }}
        />
      ))}
      <Button onClick={submitHandoff}>Complete Handoff</Button>
    </div>
  );
};
```

---

## 3. UX-011: Patient Self-Service Portal - API Mapping

### 3.1 UI Layout: Patient Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏥 SURYA PATIENT PORTAL                          Welcome, {name}! [Logout]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [🏠 Home] [📅 Appointments] [💬 Messages] [💊 Medications] [💳 Billing]   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📅 UPCOMING APPOINTMENTS                                            │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐│   │
│  │ │ {date} • {time}                                                 ││   │
│  │ │ {provider_name} - {specialty}                                   ││   │
│  │ │ {location}                                                      ││   │
│  │ │ [📍 Directions] [📅 Reschedule] [❌ Cancel]                    ││   │
│  │ └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                     [View All →]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────┐   │
│  │ 💊 MEDICATIONS                   │  │ 🧪 RECENT RESULTS           │   │
│  │ Active Prescriptions: {count}   │  │ {date} - {result_type}       │   │
│  │ • {med_name}                    │  │ {key_value}                  │   │
│  │   {instructions}                 │  │ [View Details →]             │   │
│  │ [Request Refill →]              │  │                              │   │
│  └──────────────────────────────────┘  └──────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📋 QUICK ACTIONS                                                    │   │
│  │ [📅 Book Appointment] [💬 Message Doctor] [💳 Pay Bill] [📤 Upload]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 API Mapping for Patient Portal

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Patient Login | `/portal/auth/login` | POST | Returns JWT tokens |
| Patient Profile | `/portal/profile` | GET | Patient demographics |
| Update Profile | `/portal/profile` | PATCH | Update contact info |
| Preferences | `/portal/preferences` | GET/PATCH | Communication prefs |
| Upcoming Appointments | `/appointments` | GET | status=booked, future |
| Health Summary | `/portal/health-records/summary` | GET | Conditions, allergies |
| Lab Results | `/portal/health-records/lab-results` | GET | Recent lab results |
| Visit History | `/portal/health-records` | GET | type=visit |
| Active Medications | `/portal/prescriptions` | GET | active_only=true |
| Message Threads | `/portal/messages` | GET | List conversations |
| Send Message | `/portal/messages` | POST | Create new thread |
| Reply to Thread | `/portal/messages/{id}/reply` | POST | Reply message |
| Billing Summary | `/portal/billing/summary` | GET | Balance due |
| Payment History | `/portal/billing/payments/history` | GET | Past payments |
| Make Payment | `/portal/billing/payments` | POST | Process payment |
| Notifications | `/portal/notifications` | GET | List notifications |

### 3.3 Appointment Booking API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Provider Search | `/fhir/Practitioner` | GET | Search by specialty |
| Available Slots | `/appointments/slots` | GET | Filter by provider, date |
| Book Appointment | `/appointments` | POST | Create appointment |
| Get Appointment | `/appointments/{id}` | GET | Appointment details |
| Reschedule | `/appointments/{id}/reschedule` | POST | New date/time |
| Cancel Appointment | `/appointments/{id}/cancel` | POST | Cancel with reason |
| Check-In | `/appointments/{id}/check-in` | POST | Self check-in |

### 3.4 Prescription Refill API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Active Prescriptions | `/portal/prescriptions` | GET | active_only=true |
| Request Refill | `/portal/prescriptions/refill` | POST | Refill request |
| Refill Status | `/portal/prescriptions/refills/{id}` | GET | Check status |
| Cancel Refill | `/portal/prescriptions/refills/{id}` | DELETE | Cancel request |
| Preferred Pharmacy | `/patients/{id}/pharmacy` | GET | Get pharmacy |
| Update Pharmacy | `/patients/{id}/pharmacy` | PUT | Change pharmacy |

### 3.5 TypeScript Implementation Pattern

```typescript
// Patient Portal Dashboard
const usePatientDashboard = (patientId: string) => {
  // Parallel data fetching for dashboard
  const queries = useQueries({
    queries: [
      {
        queryKey: ['upcoming-appointments', patientId],
        queryFn: () => api.get('/appointments', {
          params: { patient_id: patientId, status: 'booked', from_date: new Date() }
        })
      },
      {
        queryKey: ['health-summary', patientId],
        queryFn: () => api.get('/portal/health-records/summary')
      },
      {
        queryKey: ['recent-labs', patientId],
        queryFn: () => api.get('/portal/health-records/lab-results', {
          params: { limit: 5 }
        })
      },
      {
        queryKey: ['active-medications', patientId],
        queryFn: () => api.get('/portal/prescriptions', {
          params: { active_only: true }
        })
      },
      {
        queryKey: ['billing-summary', patientId],
        queryFn: () => api.get('/portal/billing/summary')
      },
      {
        queryKey: ['unread-messages', patientId],
        queryFn: () => api.get('/portal/messages', {
          params: { is_unread: true }
        })
      }
    ]
  });

  return {
    appointments: queries[0].data,
    healthSummary: queries[1].data,
    recentLabs: queries[2].data,
    medications: queries[3].data,
    billing: queries[4].data,
    unreadMessages: queries[5].data?.total_count || 0,
    isLoading: queries.some(q => q.isLoading)
  };
};

// Appointment Booking Flow
const AppointmentBookingWizard: React.FC = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    visit_type: '',
    provider_id: '',
    date: null,
    time: null
  });

  // Get available slots
  const { data: slots } = useQuery(
    ['available-slots', formData.provider_id, formData.date],
    () => api.get('/appointments/slots', {
      params: {
        practitioner_id: formData.provider_id,
        date: formData.date,
        duration: 30
      }
    }),
    { enabled: !!formData.provider_id && !!formData.date }
  );

  // Book appointment
  const bookAppointment = useMutation(async () => {
    const appointment = await api.post('/appointments', {
      patient_id: getCurrentPatientId(),
      practitioner_id: formData.provider_id,
      slot_id: formData.time,
      appointment_type: formData.visit_type,
      reason: formData.reason
    });
    return appointment;
  });

  return (
    <div className="booking-wizard">
      {step === 1 && (
        <VisitTypeSelection
          value={formData.visit_type}
          onChange={(type) => setFormData({ ...formData, visit_type: type })}
          onNext={() => setStep(2)}
        />
      )}
      {step === 2 && (
        <ProviderSelection
          visitType={formData.visit_type}
          value={formData.provider_id}
          onChange={(id) => setFormData({ ...formData, provider_id: id })}
          onNext={() => setStep(3)}
        />
      )}
      {step === 3 && (
        <DateTimeSelection
          providerId={formData.provider_id}
          slots={slots}
          selectedDate={formData.date}
          selectedTime={formData.time}
          onDateChange={(date) => setFormData({ ...formData, date })}
          onTimeChange={(time) => setFormData({ ...formData, time })}
          onBook={() => bookAppointment.mutate()}
        />
      )}
    </div>
  );
};

// Patient Messaging Component
const PatientMessaging: React.FC = () => {
  const [selectedThread, setSelectedThread] = useState<string | null>(null);

  // Get message threads
  const { data: threads } = useQuery(['message-threads'], () =>
    api.get('/portal/messages')
  );

  // Get thread messages
  const { data: messages } = useQuery(
    ['thread-messages', selectedThread],
    () => api.get(`/portal/messages/${selectedThread}`),
    { enabled: !!selectedThread }
  );

  // Send reply
  const sendReply = useMutation(async (content: string) => {
    return await api.post(`/portal/messages/${selectedThread}/reply`, {
      content,
      message_type: 'text'
    });
  });

  return (
    <div className="patient-messaging">
      {/* Thread list */}
      <ThreadList
        threads={threads?.threads || []}
        selectedId={selectedThread}
        onSelect={setSelectedThread}
      />

      {/* Message view */}
      {selectedThread && (
        <MessageView
          messages={messages || []}
          onSend={(content) => sendReply.mutate(content)}
        />
      )}
    </div>
  );
};
```

---

## 4. UX-012: Mobile Applications - API Mapping

### 4.1 UI Layout: Patient Mobile Home

```
┌─────────────────────────────────┐
│ ≡                  🔔 {count} 👤 │
├─────────────────────────────────┤
│                                 │
│  Good {time_of_day}, {name}!   │
│                                 │
│  ┌─────────────────────────────┐│
│  │ 📅 NEXT APPOINTMENT         ││
│  │ {date} • {time}             ││
│  │ {provider_name}             ││
│  │ {visit_type}                ││
│  │ [📍 Directions] [📅 Change]││
│  └─────────────────────────────┘│
│                                 │
│  ┌─────────────────────────────┐│
│  │ 💊 MEDICATION REMINDER      ││
│  │ {med_name}                  ││
│  │ {instructions}              ││
│  │ [✓ Taken]  [⏰ Remind Later]││
│  └─────────────────────────────┘│
│                                 │
│  ┌───────────┐  ┌───────────┐  │
│  │ 📅 Book   │  │ 💬 Message│  │
│  │ Appt      │  │ Doctor    │  │
│  └───────────┘  └───────────┘  │
│  ┌───────────┐  ┌───────────┐  │
│  │ 📋 Health │  │ 💳 Pay    │  │
│  │ Records   │  │ Bill      │  │
│  └───────────┘  └───────────┘  │
│                                 │
├─────────────────────────────────┤
│ 🏠    📅    💬    📋    ⚙️    │
│ Home  Appts Msgs  Records Set  │
└─────────────────────────────────┘
```

### 4.2 API Mapping for Mobile

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Device Registration | `/mobile/devices/register` | POST | Register device |
| Update Push Token | `/mobile/devices/{id}/token` | PUT | Update FCM/APNs token |
| Biometric Auth | `/mobile/auth/biometric` | POST | Biometric login |
| Biometric Challenge | `/mobile/auth/biometric/challenge` | POST | Get challenge |
| Create Session | `/mobile/auth/session` | POST | New mobile session |
| Refresh Session | `/mobile/auth/refresh` | POST | Refresh token |
| Get Notifications | `/mobile/notifications` | GET | User notifications |
| Mark Notification Read | `/mobile/notifications/{id}/read` | POST | Mark read |
| Notification Prefs | `/mobile/notifications/preferences` | GET/PUT | Get/update prefs |
| Pull Sync | `/mobile/sync/pull` | POST | Delta sync from server |
| Push Sync | `/mobile/sync/push` | POST | Push local changes |
| Sync Status | `/mobile/sync/status` | GET | Current sync state |
| Connect Wearable | `/mobile/wearables/connect` | POST | Connect device |
| List Wearables | `/mobile/wearables` | GET | User's wearables |
| Sync Wearable | `/mobile/wearables/{id}/sync` | POST | Sync data |
| Record Health Metric | `/mobile/health-metrics` | POST | Single metric |
| Bulk Health Metrics | `/mobile/health-metrics/bulk` | POST | Batch metrics |
| Get Health Metrics | `/mobile/health-metrics` | GET | Query metrics |
| Health Goals | `/mobile/health-goals` | GET/POST | Goals CRUD |
| Goal Progress | `/mobile/health-goals/{id}/progress` | GET | Goal progress |

### 4.3 Push Notification Integration

```typescript
// Push Notification Service
import messaging from '@react-native-firebase/messaging';
import PushNotification from 'react-native-push-notification';

class PushNotificationService {
  private deviceToken: string | null = null;

  async initialize() {
    // Request permission
    const authStatus = await messaging().requestPermission();
    if (authStatus === messaging.AuthorizationStatus.AUTHORIZED) {
      // Get FCM token
      this.deviceToken = await messaging().getToken();

      // Register with backend
      await api.post('/mobile/devices/register', {
        device_token: this.deviceToken,
        platform: Platform.OS,
        app_version: APP_VERSION,
        device_model: DeviceInfo.getModel(),
        os_version: DeviceInfo.getSystemVersion()
      });

      // Listen for token refresh
      messaging().onTokenRefresh(async (token) => {
        this.deviceToken = token;
        await api.put(`/mobile/devices/${deviceId}/token`, {
          device_token: token
        });
      });

      // Handle foreground messages
      messaging().onMessage(async (remoteMessage) => {
        this.showLocalNotification(remoteMessage);
      });

      // Handle background messages
      messaging().setBackgroundMessageHandler(async (remoteMessage) => {
        console.log('Background message:', remoteMessage);
      });
    }
  }

  private showLocalNotification(message: FirebaseMessagingTypes.RemoteMessage) {
    PushNotification.localNotification({
      channelId: 'default',
      title: message.notification?.title,
      message: message.notification?.body || '',
      data: message.data,
      userInfo: message.data
    });
  }

  async updatePreferences(prefs: NotificationPreferences) {
    return api.put('/mobile/notifications/preferences', prefs);
  }
}
```

### 4.4 Offline Sync Implementation

```typescript
// Offline Sync Service
import MMKV from 'react-native-mmkv';
import NetInfo from '@react-native-community/netinfo';

const storage = new MMKV({ id: 'offline-data', encryptionKey: ENCRYPTION_KEY });

class OfflineSyncService {
  private isOnline = true;
  private pendingChanges: SyncChange[] = [];

  constructor() {
    // Monitor connectivity
    NetInfo.addEventListener(state => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected || false;

      if (wasOffline && this.isOnline) {
        this.syncPendingChanges();
      }
    });
  }

  // Pull changes from server
  async pullChanges(entityTypes: string[]) {
    const lastSyncTimestamp = storage.getString('last_sync_timestamp');

    const response = await api.post('/mobile/sync/pull', {
      entity_types: entityTypes,
      last_sync_timestamp: lastSyncTimestamp,
      device_version: storage.getString('sync_version')
    });

    // Store data locally
    for (const entity of response.entities) {
      storage.set(`entity_${entity.type}_${entity.id}`, JSON.stringify(entity.data));
    }

    // Update sync timestamp
    storage.set('last_sync_timestamp', response.sync_timestamp);
    storage.set('sync_version', response.server_version);

    return response;
  }

  // Push local changes
  async pushChanges() {
    if (this.pendingChanges.length === 0) return;

    const response = await api.post('/mobile/sync/push', {
      changes: this.pendingChanges
    });

    // Handle conflicts
    if (response.conflicts.length > 0) {
      for (const conflict of response.conflicts) {
        await this.resolveConflict(conflict);
      }
    }

    // Clear synced changes
    this.pendingChanges = this.pendingChanges.filter(
      c => !response.synced_ids.includes(c.id)
    );
  }

  // Queue change for sync
  queueChange(change: SyncChange) {
    this.pendingChanges.push(change);
    storage.set('pending_changes', JSON.stringify(this.pendingChanges));

    if (this.isOnline) {
      this.pushChanges();
    }
  }

  // Resolve sync conflict
  async resolveConflict(conflict: SyncConflict) {
    // Default: server wins for clinical data
    if (conflict.entity_type === 'clinical') {
      await api.post(`/mobile/sync/conflicts/${conflict.id}/resolve`, {
        resolution: 'server_wins'
      });
    } else {
      // For non-clinical: client wins
      await api.post(`/mobile/sync/conflicts/${conflict.id}/resolve`, {
        resolution: 'client_wins'
      });
    }
  }

  private async syncPendingChanges() {
    const stored = storage.getString('pending_changes');
    if (stored) {
      this.pendingChanges = JSON.parse(stored);
      await this.pushChanges();
    }
  }
}
```

### 4.5 Health Data Integration

```typescript
// HealthKit / Google Fit Integration
import AppleHealthKit, { HealthValue } from 'react-native-health';
import GoogleFit from 'react-native-google-fit';

class HealthDataService {
  async initialize() {
    if (Platform.OS === 'ios') {
      await this.initializeHealthKit();
    } else {
      await this.initializeGoogleFit();
    }
  }

  private async initializeHealthKit() {
    const permissions = {
      permissions: {
        read: [
          AppleHealthKit.Constants.Permissions.HeartRate,
          AppleHealthKit.Constants.Permissions.BloodPressureSystolic,
          AppleHealthKit.Constants.Permissions.BloodPressureDiastolic,
          AppleHealthKit.Constants.Permissions.StepCount,
          AppleHealthKit.Constants.Permissions.Weight
        ]
      }
    };

    AppleHealthKit.initHealthKit(permissions, (error) => {
      if (!error) {
        this.syncHealthData();
      }
    });
  }

  private async initializeGoogleFit() {
    const options = {
      scopes: [
        GoogleFit.Scopes.FITNESS_HEART_RATE_READ,
        GoogleFit.Scopes.FITNESS_BLOOD_PRESSURE_READ,
        GoogleFit.Scopes.FITNESS_ACTIVITY_READ,
        GoogleFit.Scopes.FITNESS_BODY_READ
      ]
    };

    await GoogleFit.authorize(options);
    this.syncHealthData();
  }

  async syncHealthData() {
    const metrics: HealthMetric[] = [];

    // Get heart rate data
    const heartRates = await this.getHeartRates();
    metrics.push(...heartRates.map(hr => ({
      metric_type: 'heart_rate',
      value: hr.value,
      recorded_at: hr.timestamp,
      source: Platform.OS === 'ios' ? 'apple_health' : 'google_fit'
    })));

    // Get step count
    const steps = await this.getSteps();
    metrics.push({
      metric_type: 'steps',
      value: steps,
      recorded_at: new Date().toISOString(),
      source: Platform.OS === 'ios' ? 'apple_health' : 'google_fit'
    });

    // Sync to backend
    if (metrics.length > 0) {
      await api.post('/mobile/health-metrics/bulk', { metrics });
    }
  }

  private async getHeartRates(): Promise<HealthValue[]> {
    return new Promise((resolve) => {
      if (Platform.OS === 'ios') {
        AppleHealthKit.getHeartRateSamples({
          startDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          endDate: new Date().toISOString()
        }, (err, results) => {
          resolve(err ? [] : results);
        });
      } else {
        // Google Fit implementation
        resolve([]);
      }
    });
  }

  private async getSteps(): Promise<number> {
    return new Promise((resolve) => {
      if (Platform.OS === 'ios') {
        AppleHealthKit.getStepCount({
          date: new Date().toISOString()
        }, (err, results) => {
          resolve(err ? 0 : results.value);
        });
      } else {
        GoogleFit.getDailyStepCountSamples({
          startDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          endDate: new Date().toISOString()
        }).then(steps => {
          const total = steps.reduce((sum, s) => sum + (s.steps || 0), 0);
          resolve(total);
        });
      }
    });
  }
}
```

### 4.6 Biometric Authentication

```typescript
// Biometric Auth Service
import ReactNativeBiometrics from 'react-native-biometrics';

class BiometricAuthService {
  private biometrics = new ReactNativeBiometrics();

  async checkBiometricSupport(): Promise<{ available: boolean; type: string }> {
    const { biometryType, available } = await this.biometrics.isSensorAvailable();
    return {
      available,
      type: biometryType || 'none'
    };
  }

  async enableBiometric(userId: string) {
    // Generate key pair
    const { publicKey } = await this.biometrics.createKeys();

    // Register with backend
    await api.post('/mobile/auth/biometric/enable', {
      biometric_type: Platform.OS === 'ios' ? 'face_id' : 'fingerprint',
      public_key: publicKey
    });

    return true;
  }

  async authenticateWithBiometric(): Promise<{ success: boolean; token?: string }> {
    // Get challenge from server
    const { challenge } = await api.post('/mobile/auth/biometric/challenge');

    // Sign challenge with biometric
    const { success, signature } = await this.biometrics.createSignature({
      promptMessage: 'Authenticate to access your health records',
      payload: challenge
    });

    if (!success) {
      return { success: false };
    }

    // Verify with backend
    const response = await api.post('/mobile/auth/biometric', {
      challenge,
      signature
    });

    return {
      success: true,
      token: response.access_token
    };
  }

  async disableBiometric() {
    await this.biometrics.deleteKeys();
    await api.post('/mobile/auth/biometric/disable');
  }
}
```

---

## 5. Gap Analysis

### 5.1 APIs Already Implemented (No Backend Work Needed)

| UX Epic | Feature | Backend Status |
|---------|---------|----------------|
| UX-010 | Provider Messaging | ✅ `/collaboration/conversations/*` |
| UX-010 | Consultations | ✅ `/collaboration/consultations/*` |
| UX-010 | SBAR Handoffs | ✅ `/collaboration/handoffs/*` |
| UX-010 | On-Call Schedules | ✅ `/collaboration/oncall/*` |
| UX-010 | Clinical Alerts | ✅ `/collaboration/alerts/*` |
| UX-010 | Care Teams | ✅ `/collaboration/care-teams/*` |
| UX-011 | Patient Auth | ✅ `/portal/auth/*` |
| UX-011 | Patient Profile | ✅ `/portal/profile` |
| UX-011 | Health Records | ✅ `/portal/health-records/*` |
| UX-011 | Patient Messaging | ✅ `/portal/messages/*` |
| UX-011 | Prescriptions/Refills | ✅ `/portal/prescriptions/*` |
| UX-011 | Billing/Payments | ✅ `/portal/billing/*` |
| UX-012 | Device Management | ✅ `/mobile/devices/*` |
| UX-012 | Mobile Auth | ✅ `/mobile/auth/*` |
| UX-012 | Push Notifications | ✅ `/mobile/notifications/*` |
| UX-012 | Offline Sync | ✅ `/mobile/sync/*` |
| UX-012 | Wearables | ✅ `/mobile/wearables/*` |
| UX-012 | Health Metrics | ✅ `/mobile/health-metrics/*` |

### 5.2 Frontend-Only Implementations

| Feature | Implementation |
|---------|----------------|
| Real-time Messaging | WebSocket connection to existing backend |
| Presence Status | WebSocket heartbeat + REST API |
| Biometric Auth | react-native-biometrics + backend validation |
| HealthKit/Google Fit | react-native-health + sync to backend |
| Offline Storage | MMKV encrypted storage |
| Push Notifications | Firebase/APNs + existing backend API |
| Voice Commands | Web Speech API / react-native-voice |

### 5.3 Recommended Mobile Libraries

| Purpose | Library |
|---------|---------|
| Navigation | `@react-navigation/native` |
| State Management | `zustand` + `@tanstack/react-query` |
| Storage | `react-native-mmkv` |
| Push Notifications | `@react-native-firebase/messaging` |
| Biometrics | `react-native-biometrics` |
| Health Data | `react-native-health` (iOS), `react-native-google-fit` (Android) |
| Video Calls | `@livekit/react-native` |
| Networking | `axios` |
| Device Info | `react-native-device-info` |
| Connectivity | `@react-native-community/netinfo` |

---

## 6. Implementation Notes

### 6.1 Provider Collaboration
- Use WebSocket for real-time messaging and presence
- Implement read receipts with optimistic updates
- Support message threading for patient context
- Cache conversation list for quick access

### 6.2 Patient Portal
- Implement proper session management with refresh tokens
- Use skeleton loaders for health records
- Support deep linking for appointment confirmations
- Implement PDF generation for statements/receipts

### 6.3 Mobile Applications
- Implement proper app state management (foreground/background)
- Handle push notification deep linking
- Implement retry logic for failed syncs
- Use background fetch for periodic data refresh
- Support app pinning for security-sensitive screens

### 6.4 Security Considerations
- Encrypt all local storage
- Implement certificate pinning
- No PHI in logs or crash reports
- Implement session timeout (30 min idle)
- Support remote session termination

---

**Document Owner:** Platform Engineering Team
**Last Updated:** November 26, 2024
**Review Cycle:** Every Sprint
