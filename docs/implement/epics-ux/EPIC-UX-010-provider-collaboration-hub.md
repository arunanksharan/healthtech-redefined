# EPIC-UX-010: Provider Collaboration Hub

**Priority:** P1 | **Estimated Effort:** 3 weeks | **Dependencies:** EPIC-UX-001, EPIC-UX-004
**Theme:** Real-Time Care Team Communication and Coordination

---

## Executive Summary

This epic delivers a comprehensive collaboration platform for healthcare providers, enabling real-time messaging, specialist consultations, care team coordination, and shift handoffs. The platform supports secure HIPAA-compliant communication with patient context always available.

---

## Strategic Objectives

1. **Real-Time Communication** - Instant messaging with presence awareness
2. **Patient-Centric** - All conversations linked to patient records
3. **Structured Handoffs** - SBAR-formatted shift transitions
4. **Specialist Access** - Quick consultation requests and responses
5. **Audit Compliance** - Complete message history for compliance

---

## Backend API Dependencies

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Provider Collaboration | `/api/v1/prm/collaboration/messages` | Messaging |
| Provider Collaboration | `/api/v1/prm/collaboration/consultations` | Consult requests |
| Provider Collaboration | `/api/v1/prm/collaboration/handoffs` | Shift handoffs |
| Provider Collaboration | `/api/v1/prm/collaboration/presence` | Online status |
| Provider Collaboration | `/api/v1/prm/collaboration/on-call` | On-call schedules |

---

## User Journeys

### Journey 10.1: Provider-to-Provider Messaging

**Persona:** Dr. Sharma messaging a colleague about a patient

**Context:** Need quick consultation without formal referral

**Messaging Interface:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MESSAGES                                                   [+ New Message] │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ CONVERSATIONS                     │ Dr. Priya Mehta                        │
│                                   │ 🟢 Online                               │
│ 🔍 Search conversations...       │                                         │
│                                   │ ─────────────────────────────────────── │
│ ┌─────────────────────────────┐  │                                         │
│ │ 👩‍⚕️ Dr. Priya Mehta   🟢    │  │ Today, 2:15 PM                          │
│ │    "Sure, I can see him..." │  │                                         │
│ │    2 min ago                │  │ 👤 Re: John Doe (MRN: 12345)            │
│ └─────────────────────────────┘  │                                         │
│                                   │ Dr. Sharma: Hi Priya, I have a patient │
│ ┌─────────────────────────────┐  │ with T2DM who's not responding well to  │
│ │ 👨‍⚕️ Dr. Arun Gupta    🟡    │  │ Metformin. Would you be able to see    │
│ │    About Mr. Wilson...      │  │ him for a consult?                      │
│ │    1 hour ago               │  │                               2:15 PM ✓ │
│ └─────────────────────────────┘  │                                         │
│                                   │ Dr. Mehta: Sure, I can see him next    │
│ ┌─────────────────────────────┐  │ week. Can you send me his recent labs   │
│ │ 🏥 Cardiology Team          │  │ and A1C?                                │
│ │    "Code Blue Room 302"     │  │                               2:18 PM ✓ │
│ │    Yesterday                │  │                                         │
│ └─────────────────────────────┘  │ ─────────────────────────────────────── │
│                                   │                                         │
│ 📋 Direct Messages               │ ┌─────────────────────────────────────┐ │
│ 👥 Group Chats                   │ │ 📎 Attach │ 👤 Patient │ Type...   │ │
│ 🏥 Department Channels           │ └─────────────────────────────────────┘ │
│                                   │                                         │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

---

### Journey 10.2: Specialist Consultation Request

**Persona:** Dr. Sharma requesting formal consult from Endocrinology

**Context:** Need documented specialist opinion

**Consultation Request:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NEW CONSULTATION REQUEST                                            [✕]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Patient: John Doe (MRN: 12345)                                            │
│                                                                             │
│  ┌─── Consultation Type ───────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Specialty:     [Endocrinology ▼]                                   │   │
│  │  Priority:      ○ Routine  ● Urgent  ○ Emergent                    │   │
│  │  Consult Type:  ● Opinion only  ○ Co-management  ○ Transfer        │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─── Reason for Consultation ─────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  [Patient with T2DM not achieving glycemic control on Metformin   ] │   │
│  │  [1000mg BID. A1C remains 7.2% (target <7.0%). Experiencing GI    ] │   │
│  │  [side effects. Requesting evaluation for alternative therapy.     ] │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─── Clinical Question ───────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  [Should we switch to SGLT2 inhibitor or add to current regimen?  ] │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ☑️ Attach relevant documents:                                             │
│     • Recent A1C results                                                   │
│     • Current medication list                                               │
│     • Last 3 clinical notes                                                │
│                                                                             │
│  Assign to: [Dr. Priya Mehta (Available) ▼]                               │
│                                                                             │
│  [Cancel]                                            [Submit Consult →]    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Journey 10.3: SBAR Shift Handoff

**Persona:** Night shift nurse handing off to day shift

**Context:** End of shift, need to transfer patient information

**SBAR Handoff Interface:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SHIFT HANDOFF                                       Night → Day Shift      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  From: Nurse Sarah (Night Shift)      To: [Nurse Mike ▼] (Day Shift)      │
│  Ward: Cardiology Unit A              Time: Nov 25, 2024 - 7:00 AM         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PATIENTS TO HAND OFF (4)                                            │   │
│  │                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐│   │
│  │ │ 🛏️ Room 301 - John Doe                                    [Edit]││   │
│  │ │                                                                 ││   │
│  │ │ S - SITUATION                                                   ││   │
│  │ │ 59 y/o male admitted for CHF exacerbation. Day 3 of admission. ││   │
│  │ │                                                                 ││   │
│  │ │ B - BACKGROUND                                                  ││   │
│  │ │ History of T2DM, HTN, prior MI. On Lasix, Metoprolol, Lisinopril││   │
│  │ │                                                                 ││   │
│  │ │ A - ASSESSMENT                                                  ││   │
│  │ │ Stable overnight. I/O: +500ml. Morning weight pending.          ││   │
│  │ │ Oxygen weaned to 2L NC. No chest pain or SOB.                  ││   │
│  │ │                                                                 ││   │
│  │ │ R - RECOMMENDATION                                              ││   │
│  │ │ • Check morning weight - if down, may increase PO intake       ││   │
│  │ │ • AM labs pending - monitor K+ with Lasix                      ││   │
│  │ │ • Possible discharge today if stable                           ││   │
│  │ │                                                                 ││   │
│  │ │ ⚠️ ALERTS: Fall risk (yellow band)                              ││   │
│  │ └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐│   │
│  │ │ 🛏️ Room 302 - Jane Smith                                  [Edit]││   │
│  │ │ S: Post-op day 1 CABG...                             [Expand ▼]││   │
│  │ └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ☑️ I have reviewed all patient handoffs                                   │
│                                                                             │
│  [Save Draft]                                        [Complete Handoff →]  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Journey 10.4: On-Call Schedule Management

**Persona:** Department coordinator managing on-call coverage

**On-Call Calendar:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ON-CALL SCHEDULE: Cardiology                                November 2024  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Currently On-Call: Dr. Rohit Sharma (Until 8:00 AM)                       │
│  📞 Contact: +91 98765 43210                                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │       │ Mon 25  │ Tue 26  │ Wed 27  │ Thu 28  │ Fri 29  │ Sat-Sun │   │
│  │ ──────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────│   │
│  │       │         │         │         │         │         │         │   │
│  │ Day   │ Dr.     │ Dr.     │ Dr.     │ Dr.     │ Dr.     │ Dr.     │   │
│  │ 8A-8P │ Sharma  │ Gill    │ Sharma  │ Patel   │ Gill    │ Sharma  │   │
│  │       │         │         │         │         │         │         │   │
│  │ Night │ Dr.     │ Dr.     │ Dr.     │ Dr.     │ Dr.     │ Dr.     │   │
│  │ 8P-8A │ Gill    │ Sharma  │ Patel   │ Sharma  │ Patel   │ Gill    │   │
│  │       │         │         │         │         │         │         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [+ Add Coverage] [📅 Swap Request] [📤 Export] [🔔 Notify Changes]       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Chat Component
```typescript
interface ChatProps {
  conversationId: string;
  participants: User[];
  messages: Message[];
  patientContext?: Patient;
  onSend: (message: MessageCreate) => void;
  onAttach: (file: File) => void;
  onLinkPatient: (patientId: string) => void;
}
```

### SBAR Form Component
```typescript
interface SBARFormProps {
  patientId: string;
  fromUser: User;
  toUser?: User;
  onSubmit: (handoff: SBARHandoff) => void;
  template?: SBARTemplate;
}
```

---

## Acceptance Criteria

### AC-1: Messaging
- [ ] Real-time message delivery
- [ ] Presence indicators work
- [ ] Patient linking works
- [ ] File attachments work
- [ ] Message history persists

### AC-2: Consultations
- [ ] Request form submits correctly
- [ ] Notifications sent to consultant
- [ ] Response workflow works
- [ ] Documents attach correctly

### AC-3: Handoffs
- [ ] SBAR template works
- [ ] Multiple patients supported
- [ ] Acknowledgment workflow works
- [ ] History auditable

### AC-4: On-Call
- [ ] Schedule displays correctly
- [ ] Contact information shows
- [ ] Swap requests work
- [ ] Notifications work

---

## Success Metrics

- Message response time: <5 minutes (urgent)
- Handoff completion rate: >98%
- Consultation turnaround: <24 hours (routine)
- Provider adoption: >80%

---

**Document Owner:** Clinical Collaboration Team
**Last Updated:** November 25, 2024
**Review Cycle:** Every Sprint
