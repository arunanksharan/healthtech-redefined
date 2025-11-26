# API Mapping Document - Part 3

## UX-006: Analytics Intelligence Dashboard
## UX-007: Clinical Workflows Interface
## UX-008: Telehealth Experience
## UX-009: Billing & Revenue Portal

---

## 1. Backend API Inventory (Relevant Modules)

### 1.1 Advanced Analytics Module (`/api/v1/prm/advanced-analytics/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/dashboard/executive` | POST | Executive dashboard with KPIs |
| `/dashboard/departments` | GET | Department performance metrics |
| `/dashboard/realtime` | GET | Real-time operational dashboard |
| `/quality/measures` | GET/POST | Clinical quality measures |
| `/quality/providers/scorecards` | GET | Provider performance scorecards |
| `/quality/safety` | GET | Patient safety indicators |
| `/quality/control-chart` | POST | Statistical process control |
| `/population/risk-stratification` | GET/POST | Risk-stratified patients |
| `/population/care-gaps` | GET/POST | Care gaps for patients |
| `/population/registry/{condition}` | GET | Chronic disease registry |
| `/population/sdoh` | GET | Social determinants analysis |
| `/financial/revenue` | POST | Revenue performance summary |
| `/financial/payer-mix` | GET | Payer mix analysis |
| `/financial/denials` | POST | Denial analysis |
| `/financial/ar-aging` | GET | AR aging report |
| `/financial/cash-flow-forecast` | POST | Cash flow forecasting |
| `/operational/productivity` | POST | Department productivity |
| `/operational/resources` | GET | Resource utilization |
| `/operational/patient-flow` | POST | Patient flow analysis |
| `/operational/bottlenecks` | GET | Bottleneck identification |
| `/operational/wait-times` | GET | Wait time analytics |
| `/operational/staffing` | POST | Predictive staffing |
| `/predictive/predict` | POST | Single prediction |
| `/predictive/batch` | POST | Batch predictions |
| `/predictive/models/{model}/performance` | GET | Model performance |
| `/reports` | POST | Create custom report |
| `/reports/{report_id}/execute` | POST | Execute report |
| `/reports/{report_id}/export` | POST | Export report |
| `/reports/schedules` | POST | Schedule report |

### 1.2 Clinical Workflows Module (`/api/v1/clinical/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/prescriptions` | POST | Create prescription (e-Rx) |
| `/prescriptions/{id}` | GET | Get prescription details |
| `/prescriptions/patient/{patient_id}` | GET | Patient prescriptions |
| `/prescriptions/{id}/sign` | POST | Sign prescription |
| `/prescriptions/{id}/send` | POST | Send to pharmacy |
| `/lab-orders` | POST | Create lab order |
| `/lab-orders/{id}` | GET | Get lab order |
| `/lab-orders/patient/{patient_id}` | GET | Patient lab orders |
| `/lab-orders/{id}/results` | GET | Get lab results |
| `/imaging-orders` | POST | Create imaging order |
| `/imaging-orders/{id}` | GET | Get imaging order |
| `/referrals` | POST | Create referral |
| `/referrals/{id}` | GET | Get referral |
| `/referrals/patient/{patient_id}` | GET | Patient referrals |
| `/documentation` | POST | Create clinical note |
| `/documentation/{id}` | GET | Get clinical note |
| `/documentation/{id}/sign` | POST | Sign clinical note |
| `/vital-signs` | POST | Record vital signs |
| `/vital-signs/patient/{patient_id}` | GET | Patient vital signs |
| `/care-plans` | POST | Create care plan |
| `/care-plans/{id}` | GET | Get care plan |

### 1.3 Telehealth Module (`/api/v1/prm/telehealth/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sessions` | POST | Create video session |
| `/sessions` | GET | List active sessions |
| `/sessions/{id}` | GET | Get session details |
| `/sessions/{id}/participants` | POST | Add participant |
| `/sessions/{id}/participants` | GET | Get participants |
| `/sessions/{id}/join-token` | POST | Generate join token |
| `/sessions/{id}/participants/{pid}/joined` | POST | Mark joined |
| `/sessions/{id}/participants/{pid}/left` | POST | Mark left |
| `/sessions/{id}/participants/{pid}/media` | PATCH | Update media state |
| `/sessions/{id}/end` | POST | End session |
| `/appointments` | POST | Book telehealth appt |
| `/appointments/{id}` | GET | Get appointment |
| `/appointments/{id}/confirm` | POST | Confirm appointment |
| `/appointments/{id}/cancel` | POST | Cancel appointment |
| `/appointments/{id}/reschedule` | POST | Reschedule |
| `/appointments/available-slots` | POST | Get available slots |
| `/waiting-room` | POST | Create waiting room |
| `/waiting-room/{id}` | GET | Get waiting room |
| `/waiting-room/{id}/check-in` | POST | Patient check-in |
| `/waiting-room/{id}/device-check` | POST | Device check result |
| `/waiting-room/{id}/admit` | POST | Admit from waiting |
| `/recordings` | POST | Start recording |
| `/recordings/{id}` | GET | Get recording |
| `/recordings/{id}/consent` | POST | Record consent |
| `/analytics/session/{id}` | GET | Session analytics |
| `/analytics/metrics` | GET | Telehealth metrics |
| `/satisfaction` | POST | Submit survey |

### 1.4 Billing Module (`/api/v1/prm/billing/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/eligibility` | POST | Verify insurance eligibility |
| `/eligibility/{id}` | GET | Get eligibility result |
| `/claims` | POST | Create claim |
| `/claims` | GET | List claims |
| `/claims/{id}` | GET | Get claim details |
| `/claims/{id}` | PUT | Update claim |
| `/claims/{id}/submit` | POST | Submit claim |
| `/claims/{id}/resubmit` | POST | Resubmit claim |
| `/claims/batch-submit` | POST | Batch submit claims |
| `/denials` | GET | List denied claims |
| `/denials/{id}` | GET | Get denial details |
| `/denials/{id}/appeal` | POST | Appeal denial |
| `/payments` | POST | Process payment |
| `/payments` | GET | List payments |
| `/payments/{id}` | GET | Get payment details |
| `/statements` | POST | Generate statement |
| `/statements` | GET | List statements |
| `/statements/{id}` | GET | Get statement |
| `/payment-plans` | POST | Create payment plan |
| `/payment-plans/{id}` | GET | Get payment plan |

### 1.5 Revenue Analytics Module (`/api/v1/prm/revenue/*`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/metrics` | GET | Revenue metrics dashboard |
| `/metrics/by-department` | GET | Revenue by department |
| `/metrics/by-payer` | GET | Revenue by payer |
| `/metrics/trends` | GET | Revenue trends |
| `/ar-aging` | GET | AR aging analysis |
| `/collections` | GET | Collection rate metrics |
| `/forecast` | POST | Revenue forecasting |

---

## 2. UX-006: Analytics Intelligence Dashboard - API Mapping

### 2.1 UI Layout: Main Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ANALYTICS DASHBOARD                          [🎤 Ask anything...] [⚙️]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Good morning, {username}! Here's your daily briefing.                     │
│  📅 {date}                                                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🤖 AI INSIGHTS                                         [See All →]  │   │
│  │ • {insight_1}                                                       │   │
│  │ • {insight_2}                                                       │   │
│  │ • {insight_3}                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────────────────────┐   │
│  │ TODAY'S APPOINTMENTS │  │ REVENUE (MTD)                            │   │
│  │       {count}        │  │      ₹{amount}                           │   │
│  │   {trend}            │  │   {vs_target}                            │   │
│  │   [View Schedule]    │  │   [View Breakdown]                       │   │
│  └──────────────────────┘  └──────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐ │
│  │ PATIENT SATISFACTION │  │ WAIT TIME (AVG)      │  │ NO-SHOW RATE     │ │
│  │     {score} ⭐       │  │     {minutes} min    │  │    {percent}%    │ │
│  │   {vs_prev}          │  │   {vs_prev}          │  │   {vs_prev}      │ │
│  │   [View Feedback]    │  │   [View by Dept]     │  │   [Analyze]      │ │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ APPOINTMENT VOLUME - Last 30 Days                         [Chart]   │   │
│  │ [Daily ▼] [Export] [Compare to Last Year]                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 API Mapping for Analytics Dashboard

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Daily Briefing Header | `/auth/me` | GET | Get current user info |
| AI Insights Panel | `/advanced-analytics/dashboard/executive` | POST | Returns insights array |
| Today's Appointments | `/appointments/today` | GET | Filter by date=today |
| Revenue MTD | `/advanced-analytics/financial/revenue` | POST | period=month-to-date |
| Patient Satisfaction | `/advanced-analytics/quality/measures` | GET | measure_id=patient_satisfaction |
| Wait Time Average | `/advanced-analytics/operational/wait-times` | GET | Aggregated wait times |
| No-Show Rate | `/analytics/no-show-rate` | GET | Calculate from appointments |
| Appointment Volume Chart | `/analytics/appointments/volume` | GET | Last 30 days data |

### 2.3 TypeScript Implementation Pattern

```typescript
// Analytics Dashboard Data Fetching
const useAnalyticsDashboard = () => {
  const [dateRange, setDateRange] = useState({ start: startOfMonth(new Date()), end: new Date() });

  // Parallel data fetching for dashboard
  const dashboardQueries = useQueries({
    queries: [
      {
        queryKey: ['executive-dashboard', dateRange],
        queryFn: () => api.post('/advanced-analytics/dashboard/executive', {
          start_date: dateRange.start,
          end_date: dateRange.end,
          include_trends: true,
          include_benchmarks: true
        })
      },
      {
        queryKey: ['realtime-dashboard'],
        queryFn: () => api.get('/advanced-analytics/dashboard/realtime'),
        refetchInterval: 30000 // Refresh every 30 seconds
      },
      {
        queryKey: ['quality-measures'],
        queryFn: () => api.get('/advanced-analytics/quality/measures')
      },
      {
        queryKey: ['operational-metrics'],
        queryFn: () => api.get('/advanced-analytics/operational/wait-times')
      }
    ]
  });

  return {
    executive: dashboardQueries[0].data,
    realtime: dashboardQueries[1].data,
    quality: dashboardQueries[2].data,
    operational: dashboardQueries[3].data,
    isLoading: dashboardQueries.some(q => q.isLoading)
  };
};

// Natural Language Query Component
const AnalyticsQueryBar = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);

  const submitQuery = async () => {
    // Send to AI chat endpoint for NL processing
    const result = await api.post('/ai/chat', {
      message: query,
      context: 'analytics',
      include_visualization: true
    });
    setResponse(result);
  };

  return (
    <div className="analytics-query-bar">
      <input
        placeholder="🎤 Ask anything..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyPress={e => e.key === 'Enter' && submitQuery()}
      />
      {response && <VisualizationRenderer data={response} />}
    </div>
  );
};
```

---

## 3. UX-007: Clinical Workflows Interface - API Mapping

### 3.1 UI Layout: Prescription (e-Rx) Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NEW PRESCRIPTION                                    Patient: {name} [✕]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚠️ ALLERGIES: {allergy_list}                                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔍 Search medication...                                      [🎤]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SEARCH RESULTS                                                      │   │
│  │ ○ {drug_name} {strength} {form}                                    │   │
│  │   {type} • ₹{price}/strip                                          │   │
│  │ ● {drug_name} {strength} {form}           ← Previously Rx'd        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─── Dosage ───────────────────────────────────────────────────────────┐  │
│  │  Dose:       [{qty}] [{unit}]                                       │  │
│  │  Route:      [{route}]                                              │  │
│  │  Frequency:  [{frequency}]   or   [Custom...]                       │  │
│  │  Duration:   [{days}] days                                          │  │
│  │  💡 Quick Select: [Once daily] [Twice daily] [Three times] [PRN]   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─── Directions (SIG) ─────────────────────────────────────────────────┐  │
│  │  [{auto_generated_sig}                                              ]│  │
│  │  💡 Suggested: "{suggestion}"                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─── Quantity & Refills ───────────────────────────────────────────────┐  │
│  │  Quantity:   [{qty}] {unit} ({supply} supply)                       │  │
│  │  Refills:    [{refills}] ({total} total)                            │  │
│  │  DAW:        ☐ Dispense as Written                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─── Pharmacy ─────────────────────────────────────────────────────────┐  │
│  │  ● Patient's Preferred: {pharmacy_name}, {location}                 │  │
│  │  ○ Send to different pharmacy                                       │  │
│  │  ○ Print prescription                                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  [Cancel]                                             [Check & Prescribe]  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 API Mapping for Clinical Workflows

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Patient Allergies | `/fhir/AllergyIntolerance` | GET | patient={patient_id} |
| Drug Search | `/clinical/medications/search` | GET | q={query} |
| Previous Rx | `/prescriptions/patient/{patient_id}` | GET | Recent prescriptions |
| Drug Interactions | `/cds/drug-interactions` | POST | Check interactions |
| Create Prescription | `/clinical/prescriptions` | POST | Create new Rx |
| Sign Prescription | `/clinical/prescriptions/{id}/sign` | POST | E-signature |
| Send to Pharmacy | `/clinical/prescriptions/{id}/send` | POST | Transmit to pharmacy |
| Patient's Pharmacy | `/patients/{id}/pharmacy` | GET | Preferred pharmacy |

### 3.3 Lab Order API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Search Lab Tests | `/clinical/lab-tests/search` | GET | q={query} |
| Suggested Tests | `/cds/suggested-labs` | POST | Based on diagnosis |
| Previous Labs | `/clinical/lab-orders/patient/{id}` | GET | Recent lab orders |
| Create Lab Order | `/clinical/lab-orders` | POST | Create order |
| Sign Lab Order | `/clinical/lab-orders/{id}/sign` | POST | E-signature |
| Lab Results | `/clinical/lab-orders/{id}/results` | GET | Get results |

### 3.4 SOAP Note API Mapping

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Voice Transcription | Web Speech API | - | Frontend only |
| AI SOAP Generation | `/medical-ai/soap-note` | POST | Generate from transcript |
| Patient Vitals | `/clinical/vital-signs/patient/{id}` | GET | Auto-populate |
| Patient Medications | `/fhir/MedicationRequest` | GET | Auto-populate |
| Recent Labs | `/clinical/lab-orders/patient/{id}/results` | GET | Auto-populate |
| Save Note | `/clinical/documentation` | POST | Save draft/final |
| Sign Note | `/clinical/documentation/{id}/sign` | POST | E-signature |

### 3.5 TypeScript Implementation Pattern

```typescript
// Prescription Form Component
interface PrescriptionFormProps {
  patientId: string;
  onComplete: () => void;
}

const PrescriptionForm: React.FC<PrescriptionFormProps> = ({ patientId, onComplete }) => {
  const [selectedDrug, setSelectedDrug] = useState(null);
  const [formData, setFormData] = useState({
    dose: 1,
    unit: 'tablet',
    route: 'oral',
    frequency: 'twice_daily',
    duration: 30,
    quantity: 60,
    refills: 3,
    dispenseAsWritten: false
  });

  // Fetch patient allergies
  const { data: allergies } = useQuery(['allergies', patientId], () =>
    api.get(`/fhir/AllergyIntolerance?patient=${patientId}`)
  );

  // Check drug interactions
  const checkInteractions = useMutation(async (drugId: string) => {
    const currentMeds = await api.get(`/fhir/MedicationRequest?patient=${patientId}&status=active`);
    return api.post('/cds/drug-interactions', {
      new_medication: drugId,
      current_medications: currentMeds.entry.map(e => e.resource.medicationCodeableConcept)
    });
  });

  // Submit prescription
  const submitRx = useMutation(async () => {
    // 1. Create prescription
    const rx = await api.post('/clinical/prescriptions', {
      patient_id: patientId,
      medication: selectedDrug,
      ...formData
    });

    // 2. Sign prescription
    await api.post(`/clinical/prescriptions/${rx.id}/sign`, {
      pin: await getProviderPin()
    });

    // 3. Send to pharmacy
    await api.post(`/clinical/prescriptions/${rx.id}/send`);

    onComplete();
  });

  return (
    <div className="prescription-form">
      {/* Allergy Warning */}
      {allergies?.entry?.length > 0 && (
        <AllergyWarning allergies={allergies.entry} />
      )}

      {/* Drug Search */}
      <DrugSearchInput
        onSelect={async (drug) => {
          setSelectedDrug(drug);
          const interactions = await checkInteractions.mutateAsync(drug.id);
          if (interactions.alerts.length > 0) {
            showInteractionDialog(interactions.alerts);
          }
        }}
      />

      {/* Dosage Form */}
      <DosageSection formData={formData} onChange={setFormData} />

      {/* Submit */}
      <Button onClick={() => submitRx.mutate()}>Check & Prescribe</Button>
    </div>
  );
};
```

---

## 4. UX-008: Telehealth Experience - API Mapping

### 4.1 UI Layout: Provider Telehealth Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TODAY'S TELEHEALTH                                          {date}          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🟢 {waiting_count} Patients Waiting  📅 {total_sessions} Sessions Today   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ WAITING NOW                                                         │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐│   │
│  │ │ 👤 {patient_name}                                  ⏱️ {wait_min}││   │
│  │ │    {reason} • {scheduled_time}                                  ││   │
│  │ │    {device_status_icon} {device_status}                         ││   │
│  │ │    [📋 View Chart] [📝 Pre-visit Notes]    [▶️ Start Session]  ││   │
│  │ └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ UPCOMING                                                            │   │
│  │ {time} │ {patient_name} │ {visit_type} │ {status_icon} {status}    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 UI Layout: Active Video Call

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TELEHEALTH SESSION                                 ⏱️ {duration} │ 🔴 REC  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐
│  │                                                                         │
│  │                         PATIENT VIDEO                                   │
│  │                         ({patient_name})                                │
│  │                                                                         │
│  │                                               ┌─────────────────────┐   │
│  │                                               │    Your Video       │   │
│  │                                               │    (PIP)            │   │
│  │                                               └─────────────────────┘   │
│  │                                                                         │
│  └─────────────────────────────────────────────────────────────────────────┘
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐
│  │  [🎤 Mute]  [📹 Video]  [🖥️ Share]  [📋 Chart]  [💊 Rx]  [🔴 End]     │
│  └─────────────────────────────────────────────────────────────────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 API Mapping for Telehealth

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Waiting Patients | `/telehealth/waiting-room` | GET | status=waiting |
| Patient Device Status | `/telehealth/waiting-room/{id}` | GET | device_check_result |
| Today's Sessions | `/telehealth/appointments` | GET | date=today |
| Start Session | `/telehealth/sessions` | POST | Create session |
| Generate Join Token | `/telehealth/sessions/{id}/join-token` | POST | For LiveKit |
| Add Participant | `/telehealth/sessions/{id}/participants` | POST | Join patient |
| Update Media State | `/telehealth/sessions/{id}/participants/{pid}/media` | PATCH | Mute/unmute |
| Start Recording | `/telehealth/recordings` | POST | Begin recording |
| Recording Consent | `/telehealth/recordings/{id}/consent` | POST | Patient consent |
| End Session | `/telehealth/sessions/{id}/end` | POST | Complete session |
| Session Analytics | `/telehealth/analytics/session/{id}` | GET | Duration, quality |
| Submit Survey | `/telehealth/satisfaction` | POST | Patient feedback |

### 4.4 TypeScript Implementation Pattern

```typescript
// Telehealth Video Component with LiveKit
import { LiveKitRoom, VideoConference } from '@livekit/components-react';

interface TelehealthVideoProps {
  sessionId: string;
  role: 'provider' | 'patient';
  onEnd: () => void;
}

const TelehealthVideo: React.FC<TelehealthVideoProps> = ({ sessionId, role, onEnd }) => {
  const [token, setToken] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  // Get join token
  useEffect(() => {
    const getToken = async () => {
      const response = await api.post(`/telehealth/sessions/${sessionId}/join-token`, {
        participant_id: getCurrentUserId()
      });
      setToken(response.token);
    };
    getToken();
  }, [sessionId]);

  // Start recording (provider only)
  const startRecording = async () => {
    await api.post('/telehealth/recordings', {
      session_id: sessionId,
      consent_obtained: true
    });
    setIsRecording(true);
  };

  // End session
  const endSession = async () => {
    await api.post(`/telehealth/sessions/${sessionId}/end`, {
      reason: 'completed'
    });
    onEnd();
  };

  if (!token) return <LoadingSpinner />;

  return (
    <LiveKitRoom
      token={token}
      serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
      connect={true}
    >
      <VideoConference />

      <div className="telehealth-controls">
        <MuteButton />
        <VideoToggle />
        <ScreenShareButton />

        {role === 'provider' && (
          <>
            <Button onClick={() => setShowChart(true)}>📋 Chart</Button>
            <Button onClick={() => setShowRx(true)}>💊 Rx</Button>
            {!isRecording && (
              <Button onClick={startRecording}>⏺️ Record</Button>
            )}
          </>
        )}

        <Button variant="danger" onClick={endSession}>🔴 End</Button>
      </div>

      {isRecording && <RecordingIndicator />}
    </LiveKitRoom>
  );
};
```

---

## 5. UX-009: Billing & Revenue Portal - API Mapping

### 5.1 UI Layout: Insurance Eligibility

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ INSURANCE ELIGIBILITY                              Patient: {patient_name}  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PRIMARY INSURANCE                                                   │   │
│  │ 🏢 {payer_name}                                                     │   │
│  │ Member ID: {member_id}                                              │   │
│  │ Group: {group_number}                                               │   │
│  │ Subscriber: {subscriber_name} ({relationship})                      │   │
│  │ Last Verified: {last_verified_date}                                 │   │
│  │ [🔄 Verify Now]                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ✅ ELIGIBILITY VERIFIED                            {verified_time}  │   │
│  │ ┌───────────────────────────────────────────────────────────────┐  │   │
│  │ │ Coverage Status      │ {status_icon} {status}                 │  │   │
│  │ │ Effective Date       │ {effective_date}                       │  │   │
│  │ │ Term Date            │ {term_date}                            │  │   │
│  │ │ Plan Type            │ {plan_type}                            │  │   │
│  │ └───────────────────────────────────────────────────────────────┘  │   │
│  │ ┌───────────────────────────────────────────────────────────────┐  │   │
│  │ │ BENEFITS FOR: {service_type}                                  │  │   │
│  │ │ Copay:              ₹{copay}                                  │  │   │
│  │ │ Deductible:         ₹{deductible} (Met: ₹{met} / Rem: ₹{rem})│  │   │
│  │ │ Coinsurance:        {coinsurance}% after deductible           │  │   │
│  │ │ Out-of-Pocket Max:  ₹{oop_max} (Met: ₹{oop_met})             │  │   │
│  │ │ Prior Auth Required: {prior_auth}                             │  │   │
│  │ └───────────────────────────────────────────────────────────────┘  │   │
│  │ 💰 COLLECT TODAY: ₹{amount_due} ({reason})                         │   │
│  │ [📥 Save to Record] [💳 Collect Payment] [📄 Print Summary]        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 API Mapping for Billing

| UI Component | API Endpoint | Method | Notes |
|--------------|--------------|--------|-------|
| Patient Insurance | `/patients/{id}/insurance` | GET | Get insurance info |
| Verify Eligibility | `/billing/eligibility` | POST | Real-time verification |
| Get Eligibility Result | `/billing/eligibility/{id}` | GET | Get cached result |
| Claims List | `/billing/claims` | GET | Filter by status, date |
| Create Claim | `/billing/claims` | POST | Create new claim |
| Get Claim Details | `/billing/claims/{id}` | GET | Full claim info |
| Submit Claim | `/billing/claims/{id}/submit` | POST | Submit to payer |
| Resubmit Claim | `/billing/claims/{id}/resubmit` | POST | Resubmit corrected |
| Denial List | `/billing/denials` | GET | List denied claims |
| Appeal Denial | `/billing/denials/{id}/appeal` | POST | File appeal |
| Process Payment | `/billing/payments` | POST | Take payment |
| Generate Statement | `/billing/statements` | POST | Generate patient bill |
| Create Payment Plan | `/billing/payment-plans` | POST | Setup payment plan |
| Revenue Metrics | `/revenue/metrics` | GET | Dashboard metrics |
| Revenue by Dept | `/revenue/metrics/by-department` | GET | Dept breakdown |
| AR Aging | `/revenue/ar-aging` | GET | AR aging report |

### 5.3 TypeScript Implementation Pattern

```typescript
// Eligibility Verification Component
const EligibilityVerification: React.FC<{ patientId: string }> = ({ patientId }) => {
  const [verificationResult, setVerificationResult] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);

  // Get patient's insurance
  const { data: insurance } = useQuery(['insurance', patientId], () =>
    api.get(`/patients/${patientId}/insurance`)
  );

  // Verify eligibility
  const verifyEligibility = async (serviceType: string = '99213') => {
    setIsVerifying(true);
    try {
      const result = await api.post('/billing/eligibility', {
        patient_id: patientId,
        payer_id: insurance.primary.payer_id,
        member_id: insurance.primary.member_id,
        service_type_code: serviceType,
        date_of_service: new Date().toISOString()
      });
      setVerificationResult(result);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="eligibility-panel">
      {/* Insurance Info Card */}
      <InsuranceCard insurance={insurance?.primary} />

      {/* Verify Button */}
      <Button
        onClick={() => verifyEligibility()}
        loading={isVerifying}
      >
        🔄 Verify Now
      </Button>

      {/* Results */}
      {verificationResult && (
        <EligibilityResults
          result={verificationResult}
          onCollectPayment={(amount) => {
            // Open payment modal
            setPaymentAmount(amount);
            setShowPaymentModal(true);
          }}
        />
      )}
    </div>
  );
};

// Claims Dashboard Component
const ClaimsDashboard: React.FC = () => {
  const [filters, setFilters] = useState({
    status: null,
    date_from: null,
    date_to: null,
    payer: null
  });

  // Fetch claims with filters
  const { data: claims, isLoading } = useQuery(
    ['claims', filters],
    () => api.get('/billing/claims', { params: filters })
  );

  // Claims summary
  const { data: summary } = useQuery(['claims-summary'], () =>
    api.get('/billing/claims/summary')
  );

  return (
    <div className="claims-dashboard">
      {/* Summary Cards */}
      <div className="summary-grid">
        <StatCard title="Pending" value={summary?.pending_count} amount={summary?.pending_amount} />
        <StatCard title="Submitted" value={summary?.submitted_count} amount={summary?.submitted_amount} />
        <StatCard title="Denied" value={summary?.denied_count} amount={summary?.denied_amount} status="warning" />
        <StatCard title="Paid" value={summary?.paid_count} amount={summary?.paid_amount} status="success" />
      </div>

      {/* Filters */}
      <ClaimsFilters filters={filters} onChange={setFilters} />

      {/* Claims Table */}
      <ClaimsTable
        claims={claims?.items || []}
        loading={isLoading}
        onViewClaim={(id) => router.push(`/billing/claims/${id}`)}
        onResubmit={(id) => resubmitClaim(id)}
      />
    </div>
  );
};
```

---

## 6. Gap Analysis

### 6.1 APIs Already Implemented (No Backend Work Needed)

| UX Epic | Feature | Backend Status |
|---------|---------|----------------|
| UX-006 | Executive Dashboard | ✅ `/advanced-analytics/dashboard/executive` |
| UX-006 | Quality Measures | ✅ `/advanced-analytics/quality/measures` |
| UX-006 | Financial Analytics | ✅ `/advanced-analytics/financial/*` |
| UX-006 | Operational Metrics | ✅ `/advanced-analytics/operational/*` |
| UX-006 | Predictive Analytics | ✅ `/advanced-analytics/predictive/*` |
| UX-007 | Prescriptions | ✅ `/clinical/prescriptions` |
| UX-007 | Lab Orders | ✅ `/clinical/lab-orders` |
| UX-007 | Clinical Documentation | ✅ `/clinical/documentation` |
| UX-007 | Vital Signs | ✅ `/clinical/vital-signs` |
| UX-007 | Referrals | ✅ `/clinical/referrals` |
| UX-008 | Video Sessions | ✅ `/telehealth/sessions` |
| UX-008 | Waiting Room | ✅ `/telehealth/waiting-room` |
| UX-008 | Appointments | ✅ `/telehealth/appointments` |
| UX-008 | Recordings | ✅ `/telehealth/recordings` |
| UX-009 | Eligibility | ✅ `/billing/eligibility` |
| UX-009 | Claims Management | ✅ `/billing/claims` |
| UX-009 | Payments | ✅ `/billing/payments` |
| UX-009 | Revenue Metrics | ✅ `/revenue/metrics` |

### 6.2 Minor Frontend Enhancements (No Backend Changes)

| Feature | Solution |
|---------|----------|
| AI Insights Generation | Frontend LLM integration for NL queries |
| Voice Dictation | Web Speech API on frontend |
| Chart Visualizations | Use Recharts/Chart.js with existing data |
| Real-time Updates | WebSocket/SSE integration with existing endpoints |
| Dashboard Customization | LocalStorage/IndexedDB for user preferences |
| Drug Interaction UI | Display alerts from existing CDS endpoint |
| Payment Processing | Integrate with payment gateway (Stripe/Razorpay) |

### 6.3 Recommended Frontend Libraries

| Purpose | Library |
|---------|---------|
| Video Calls | `@livekit/components-react` |
| Charts | `recharts` or `@nivo/core` |
| Data Tables | `@tanstack/react-table` |
| Form Handling | `react-hook-form` + `zod` |
| Date Handling | `date-fns` |
| Speech Recognition | Web Speech API / `@speechly/react-client` |
| PDF Generation | `@react-pdf/renderer` |
| Real-time | Native WebSocket or `socket.io-client` |

---

## 7. Implementation Notes

### 7.1 Analytics Dashboard
- Use `Promise.all` to fetch multiple metrics in parallel
- Implement caching with React Query's `staleTime`
- Add skeleton loaders for each metric card
- Support dashboard customization via drag-and-drop (react-dnd)

### 7.2 Clinical Workflows
- Implement auto-save for clinical notes (debounced)
- Use optimistic updates for better UX
- Integrate drug interaction alerts inline with prescription form
- Support voice dictation with real-time transcription display

### 7.3 Telehealth
- Use LiveKit for video calls (HIPAA-compliant)
- Implement reconnection logic for dropped connections
- Support picture-in-picture mode
- Show network quality indicators during calls

### 7.4 Billing
- Cache eligibility results for same-day verifications
- Implement claim validation before submission
- Support batch claim operations
- Provide real-time payment confirmation

---

**Document Owner:** Frontend Architecture Team
**Last Updated:** November 26, 2024
**Review Cycle:** Every Sprint
