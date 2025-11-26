# EPIC-UX-012: Mobile Applications

**Priority:** P0 | **Estimated Effort:** 6 weeks | **Dependencies:** EPIC-UX-001, EPIC-UX-011
**Theme:** Native Mobile Experience for Patients and Providers

---

## Executive Summary

This epic delivers native mobile applications for iOS and Android using React Native, providing both patient-facing and provider-facing experiences. The apps support offline functionality, push notifications, biometric authentication, and device health integration. The goal is to extend the PRM platform to mobile devices with a seamless, native experience.

---

## Strategic Objectives

1. **Native Experience** - Platform-specific UI patterns for iOS and Android
2. **Offline-First** - Key features work without internet connection
3. **Push Engagement** - Timely notifications for appointments, messages, alerts
4. **Health Integration** - Apple HealthKit and Google Fit integration
5. **Security** - Biometric authentication, secure storage, remote wipe

---

## Backend API Dependencies

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Mobile | `/api/v1/prm/mobile/devices` | Device registration |
| Mobile | `/api/v1/prm/mobile/push` | Push notifications |
| Mobile | `/api/v1/prm/mobile/sync` | Offline sync |
| Mobile | `/api/v1/prm/mobile/health` | Health data sync |
| Patient Portal | `/api/v1/prm/portal/*` | Patient features |
| Provider Collaboration | `/api/v1/prm/collaboration/*` | Provider features |

---

## App Architecture

### Technology Stack
- **Framework:** React Native 0.73+
- **Navigation:** React Navigation 6
- **State:** Zustand + TanStack Query
- **Storage:** MMKV (encrypted local storage)
- **Push:** Firebase Cloud Messaging (FCM) + Apple Push Notification (APNs)
- **Health:** react-native-health (HealthKit/Google Fit)
- **Auth:** Biometrics via react-native-biometrics

---

## Patient Mobile App

### Journey 12.1: Patient App Onboarding

**Flow:**
```
Download App → Open → Login/Register → Biometric Setup →
Notification Permission → Health Integration → Home Screen
```

**Onboarding Screens:**

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│                         │  │                         │  │                         │
│                         │  │                         │  │                         │
│     🏥                  │  │     🔐                  │  │     🔔                  │
│                         │  │                         │  │                         │
│   Your Health,         │  │   Secure Access         │  │   Stay Informed         │
│   Your Way             │  │                         │  │                         │
│                         │  │   Use Face ID or       │  │   Get reminders for     │
│   Access your health   │  │   fingerprint for       │  │   appointments and      │
│   records, book        │  │   quick, secure         │  │   important health      │
│   appointments, and    │  │   access to your        │  │   updates               │
│   message your doctor  │  │   health data           │  │                         │
│   - all from your      │  │                         │  │                         │
│   phone                │  │                         │  │                         │
│                         │  │                         │  │                         │
│   ○ ○ ●                │  │   [Enable Face ID]     │  │   [Enable Notifications]│
│                         │  │   [Skip for now]       │  │   [Not now]             │
│   [Get Started]        │  │                         │  │                         │
│                         │  │                         │  │                         │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

### Journey 12.2: Patient Home Screen

**Mobile Dashboard:**

```
┌─────────────────────────────────────┐
│ ≡                      🔔 2    👤  │
├─────────────────────────────────────┤
│                                     │
│  Good morning, John!                │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 📅 NEXT APPOINTMENT             ││
│  │                                 ││
│  │ Dec 23, 2024 • 2:00 PM         ││
│  │ Dr. Rohit Sharma               ││
│  │ Cardiology Follow-up           ││
│  │                                 ││
│  │ [📍 Directions]  [📅 Reschedule]││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 💊 MEDICATION REMINDER          ││
│  │                                 ││
│  │ Metformin 1000mg               ││
│  │ Take with dinner               ││
│  │                                 ││
│  │ [✓ Taken]     [⏰ Remind Later]││
│  └─────────────────────────────────┘│
│                                     │
│  ┌───────────┐  ┌───────────┐      │
│  │ 📅 Book   │  │ 💬 Message│      │
│  │ Appt      │  │ Doctor    │      │
│  └───────────┘  └───────────┘      │
│  ┌───────────┐  ┌───────────┐      │
│  │ 📋 Health │  │ 💳 Pay    │      │
│  │ Records   │  │ Bill      │      │
│  └───────────┘  └───────────┘      │
│                                     │
├─────────────────────────────────────┤
│ 🏠    📅    💬    📋    ⚙️        │
│ Home  Appts Msgs  Records Settings │
└─────────────────────────────────────┘
```

### Journey 12.3: Telehealth on Mobile

**Video Call Interface (Patient):**

```
┌─────────────────────────────────────┐
│                    ⏱️ 08:45  🔴 REC │
├─────────────────────────────────────┤
│                                     │
│                                     │
│                                     │
│       ┌───────────────────┐         │
│       │                   │         │
│       │   DR. SHARMA      │         │
│       │   VIDEO           │         │
│       │                   │         │
│       │                   │         │
│       └───────────────────┘         │
│                                     │
│                                     │
│                 ┌───────────┐       │
│                 │   YOU     │       │
│                 └───────────┘       │
│                                     │
├─────────────────────────────────────┤
│                                     │
│    🎤      📹      💬      📞      │
│   Mute   Video   Chat    End       │
│                                     │
└─────────────────────────────────────┘
```

### Journey 12.4: Health Data Sync

**Apple Health Integration:**

```
┌─────────────────────────────────────┐
│ ←    HEALTH INTEGRATION            │
├─────────────────────────────────────┤
│                                     │
│  Connect your health apps to       │
│  share data with your care team    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ❤️ Apple Health         [ON]   ││
│  │                                 ││
│  │ Syncing:                        ││
│  │ ☑️ Heart Rate                   ││
│  │ ☑️ Blood Pressure               ││
│  │ ☑️ Steps                        ││
│  │ ☑️ Weight                       ││
│  │ ☐ Sleep Analysis                ││
│  │                                 ││
│  │ Last synced: 5 min ago         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 📊 RECENT DATA                  ││
│  │                                 ││
│  │ Today's Steps     8,432        ││
│  │ Avg Heart Rate    72 bpm       ││
│  │ Blood Pressure    128/82       ││
│  │ Weight            185 lbs      ││
│  └─────────────────────────────────┘│
│                                     │
│  ℹ️ Your doctor can view this data │
│     to better manage your care     │
│                                     │
└─────────────────────────────────────┘
```

---

## Provider Mobile App

### Journey 12.5: Provider Quick Actions

**Provider Home Screen:**

```
┌─────────────────────────────────────┐
│ ≡                      🔔 5    👤  │
├─────────────────────────────────────┤
│                                     │
│  Good morning, Dr. Sharma!         │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ TODAY'S SCHEDULE                ││
│  │                                 ││
│  │ 14 Appointments | 3 Telehealth ││
│  │                                 ││
│  │ Next: 9:00 AM - John Doe       ││
│  │       Cardiology Follow-up     ││
│  │                                 ││
│  │ [View Full Schedule →]         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ⚠️ ALERTS (3)                   ││
│  │                                 ││
│  │ 🔴 Critical lab - Mary J.      ││
│  │ 🟡 Consult request - Dr. Patel ││
│  │ 🟡 Rx refill needed - Bob W.   ││
│  │                                 ││
│  │ [View All →]                   ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌───────────┐  ┌───────────┐      │
│  │ 👥 Patient│  │ 💬 Messages│      │
│  │ Lookup    │  │    (12)   │      │
│  └───────────┘  └───────────┘      │
│  ┌───────────┐  ┌───────────┐      │
│  │ 📞 On-Call│  │ 📋 Tasks  │      │
│  │ Schedule  │  │    (5)    │      │
│  └───────────┘  └───────────┘      │
│                                     │
├─────────────────────────────────────┤
│ 🏠    📅    👥    💬    ⚙️        │
│ Home  Sched Patient Msgs Settings  │
└─────────────────────────────────────┘
```

### Journey 12.6: Mobile Patient Lookup

**Quick Patient Search:**

```
┌─────────────────────────────────────┐
│ ←    PATIENT SEARCH                │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 🔍 Search by name, MRN, phone  ││
│  │    John                         ││
│  └─────────────────────────────────┘│
│                                     │
│  RESULTS                            │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👤 John Doe                     ││
│  │    MRN: 12345 | 59 y/o M       ││
│  │    📅 Last: Nov 20, 2024       ││
│  │    ⚠️ Allergies: Penicillin    ││
│  │                            [→] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👤 John Smith                   ││
│  │    MRN: 67890 | 45 y/o M       ││
│  │    📅 Last: Oct 5, 2024        ││
│  │                            [→] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👤 Johnny Williams              ││
│  │    MRN: 11111 | 32 y/o M       ││
│  │    📅 Last: Sep 15, 2024       ││
│  │                            [→] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### Journey 12.7: Mobile Patient Chart

**Simplified Chart View:**

```
┌─────────────────────────────────────┐
│ ←    John Doe                  ⋮   │
├─────────────────────────────────────┤
│                                     │
│  ┌───────┐  John Doe               │
│  │  👤   │  59 y/o Male | MRN: 12345│
│  └───────┘  📱 +91 98441 11173     │
│                                     │
│  ⚠️ Allergy: Penicillin (Severe)   │
│                                     │
├─────────────────────────────────────┤
│ [Summary] [Vitals] [Labs] [Meds]   │
├─────────────────────────────────────┤
│                                     │
│  CONDITIONS                         │
│  • Type 2 Diabetes Mellitus        │
│  • Essential Hypertension          │
│  • Hyperlipidemia                  │
│                                     │
│  RECENT VITALS (Nov 25)            │
│  BP: 138/88 | HR: 76 | Wt: 185    │
│                                     │
│  RECENT LABS (Nov 25)              │
│  A1C: 7.2% 🟡                      │
│  [View All Labs →]                 │
│                                     │
│  MEDICATIONS                        │
│  • Metformin 1000mg BID            │
│  • Lisinopril 10mg daily           │
│                                     │
├─────────────────────────────────────┤
│ [📞 Call] [💬 Message] [💊 Rx]     │
└─────────────────────────────────────┘
```

---

## Push Notification Specifications

### Notification Types

| Type | Title | Body | Action |
|------|-------|------|--------|
| Appointment Reminder | "Appointment Tomorrow" | "Your appointment with Dr. Sharma is tomorrow at 2:00 PM" | Open appointment details |
| Telehealth Ready | "Doctor is Ready" | "Dr. Sharma is ready for your video visit. Tap to join." | Join telehealth |
| Message | "New Message" | "Dr. Sharma's office sent you a message" | Open messages |
| Lab Results | "Lab Results Ready" | "Your lab results are now available" | Open results |
| Medication Reminder | "Time for Medication" | "Take Metformin 1000mg with dinner" | Mark as taken |
| Bill Due | "Payment Due Soon" | "Your balance of ₹1,250 is due on Dec 15" | Open billing |

### Provider Notifications

| Type | Title | Body | Action |
|------|-------|------|--------|
| Critical Result | "🔴 Critical Lab Result" | "Critical value for John Doe - Potassium 6.2" | View result |
| Consult Request | "New Consult Request" | "Dr. Patel requested a consult for Mary Johnson" | View consult |
| Patient Message | "Patient Message" | "John Doe sent a message" | Reply |
| Schedule Change | "Schedule Updated" | "Tomorrow's 2PM appointment cancelled" | View schedule |

---

## Offline Functionality

### Patient App Offline Features
- View cached appointments
- View cached health records
- View medication list
- Draft messages (send when online)
- View downloaded documents

### Provider App Offline Features
- View cached patient summaries
- View today's schedule
- Draft clinical notes
- View downloaded protocols
- Access emergency contacts

### Sync Strategy
```typescript
interface SyncConfig {
  // Sync on app open
  onAppOpen: boolean;
  // Sync interval (minutes)
  backgroundInterval: number;
  // Sync on connectivity restore
  onConnectivityRestore: boolean;
  // Data expiration (hours)
  cacheExpiration: number;
}
```

---

## Security Requirements

1. **Biometric Authentication**
   - Face ID / Touch ID required after app backgrounded >5 min
   - Optional PIN fallback
   - Automatic logout after 30 min inactive

2. **Secure Storage**
   - Encrypted local database (MMKV)
   - No PHI in logs or crash reports
   - Secure keychain for tokens

3. **Remote Management**
   - Remote session termination
   - Remote data wipe capability
   - Device registration management

4. **Network Security**
   - Certificate pinning
   - TLS 1.3 required
   - No data on insecure networks

---

## Acceptance Criteria

### AC-1: Patient App
- [ ] Onboarding flow completes
- [ ] Biometric setup works
- [ ] Push notifications received
- [ ] Appointment booking works
- [ ] Messaging works
- [ ] Telehealth joins successfully
- [ ] Health data syncs
- [ ] Offline mode works

### AC-2: Provider App
- [ ] Schedule displays correctly
- [ ] Patient search works
- [ ] Chart view loads
- [ ] Alerts display and action
- [ ] Messages work
- [ ] Push notifications work
- [ ] Offline mode works

### AC-3: Performance
- [ ] App launch < 2 seconds
- [ ] Screen transitions < 300ms
- [ ] Search results < 1 second
- [ ] Sync completes < 5 seconds

### AC-4: Security
- [ ] Biometric auth works
- [ ] Session timeout works
- [ ] Secure storage verified
- [ ] Remote wipe works

---

## Success Metrics

- App store rating: >4.5 stars
- Daily active users: >50% of registered
- Push notification opt-in: >80%
- Telehealth join rate (mobile): >90%
- Crash-free rate: >99.5%

---

**Document Owner:** Mobile Product Team
**Last Updated:** November 25, 2024
**Review Cycle:** Every Sprint
