# EPIC-UX-002: Omni-Inbox & Live Feed

**Priority:** P0 | **Estimated Effort:** 4 weeks | **Dependencies:** EPIC-UX-001
**Theme:** The Central Nervous System - Real-time unified activity stream

---

## Executive Summary

The Omni-Inbox replaces the traditional dashboard as the landing page for healthcare staff. It provides a unified, real-time feed of all patient interactions across channels (Zoice voice calls, WhatsApp messages, app interactions, system events) in a single, actionable interface. This is the "Twitter/Facebook feed for hospital operations" - where every patient touchpoint surfaces as an actionable card.

---

## Strategic Objectives

1. **Unified View** - Single pane of glass for all patient communications
2. **Real-Time** - Instant visibility into incoming interactions via WebSocket
3. **Actionable** - Every feed item surfaces suggested next actions
4. **Contextual** - Click any card to reveal relevant details and actions
5. **Intelligent** - AI-powered sentiment analysis, priority scoring, and routing

---

## Backend API Dependencies

This epic integrates with the following backend services:

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Omnichannel | `/api/v1/prm/omnichannel/inbox` | Unified inbox messages |
| Omnichannel | `/api/v1/prm/omnichannel/conversations` | Conversation threads |
| Voice Webhooks | `/api/v1/prm/voice/calls` | Zoice call transcripts |
| WhatsApp Webhooks | `/api/v1/prm/whatsapp/messages` | WhatsApp messages |
| AI Platform | `/api/v1/prm/ai/analyze` | Sentiment & intent analysis |
| FHIR | `/api/v1/prm/fhir/Patient` | Patient context |
| Notifications | WebSocket | Real-time event stream |

---

## User Journeys

### Journey 2.1: Morning Inbox Review

**Persona:** Front Desk Receptionist starting their shift

**Context:** Sarah arrives at 8 AM and opens the PRM to catch up on overnight activity

**Flow:**
```
Login → Omni-Inbox Landing → Filter: Unread → Review Cards →
Take Action → Mark Resolved → Continue to Next
```

**Detailed Experience:**

1. **Landing State**
   ```
   ┌─────────────────────────────────────────────────────────────────────┐
   │ SIDEBAR │           LIVE FEED (Main)           │   CONTEXT PANEL   │
   │         │                                       │                   │
   │ [Nav]   │  Good morning, Sarah! 👋              │   [Empty state]   │
   │         │  You have 12 unread items             │                   │
   │         │  ──────────────────────────           │   Select an item  │
   │         │                                       │   to see details  │
   │         │  [Filter: All ▼] [Unread Only ☑️]     │                   │
   │         │                                       │                   │
   │         │  ┌─────────────────────────────────┐  │                   │
   │         │  │ 🎤 ZOICE CALL - 7:45 AM         │  │                   │
   │         │  │ John Doe • Cardiology           │  │                   │
   │         │  │ 😤 Frustrated • Rescheduling    │  │                   │
   │         │  │ "...can't make tomorrow's..."   │  │                   │
   │         │  └─────────────────────────────────┘  │                   │
   │         │                                       │                   │
   │         │  ┌─────────────────────────────────┐  │                   │
   │         │  │ 💬 WHATSAPP - 7:30 AM           │  │                   │
   │         │  │ Jane Smith • Insurance Upload   │  │                   │
   │         │  │ 😊 Positive • Document Sent     │  │                   │
   │         │  │ [📎 insurance_card.jpg]         │  │                   │
   │         │  └─────────────────────────────────┘  │                   │
   └─────────────────────────────────────────────────────────────────────┘
   ```

2. **Feed Card Anatomy**
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │ [Channel Icon] [Channel Name] - [Timestamp]      [●] [Priority] │
   ├─────────────────────────────────────────────────────────────────┤
   │ [Patient Avatar] Patient Name • Department/Context              │
   │ [Sentiment Emoji] Sentiment Label • Intent Label                │
   │ "[Truncated message preview or call summary...]"                │
   │ [Attachment Previews if any]                                    │
   ├─────────────────────────────────────────────────────────────────┤
   │ [Quick Action 1] [Quick Action 2]              [View Details →] │
   └─────────────────────────────────────────────────────────────────┘
   ```

3. **Click to Expand - Context Panel**
   When Sarah clicks the Zoice call card:
   ```
   ┌─────────────────────────────────────────┐
   │ CALL DETAILS                    [✕]    │
   ├─────────────────────────────────────────┤
   │ 👤 John Doe                            │
   │ 📞 +1 (555) 123-4567                   │
   │ 🏥 Cardiology - Dr. Sharma             │
   ├─────────────────────────────────────────┤
   │ 📊 CALL ANALYSIS                       │
   │                                         │
   │ Sentiment:     😤 Frustrated (87%)     │
   │ Intent:        Reschedule Appointment   │
   │ Urgency:       🔴 High                  │
   │ Duration:      4m 32s                   │
   ├─────────────────────────────────────────┤
   │ 📝 AI SUMMARY                          │
   │                                         │
   │ Patient called to reschedule           │
   │ tomorrow's 2PM cardiology follow-up.   │
   │ Expressed frustration about traffic.   │
   │ Requested Tuesday or Wednesday         │
   │ afternoon instead.                     │
   ├─────────────────────────────────────────┤
   │ 🎯 SUGGESTED ACTIONS                   │
   │                                         │
   │ [📅 Reschedule to Tue 2PM]  ← Primary  │
   │ [📅 Reschedule to Wed 3PM]             │
   │ [📞 Callback Patient]                  │
   │ [💬 Send WhatsApp Confirmation]        │
   ├─────────────────────────────────────────┤
   │ 🎧 LISTEN TO RECORDING                 │
   │ ▶ ━━━━━━━━━━━●━━━━━━━ 4:32            │
   ├─────────────────────────────────────────┤
   │ 📄 FULL TRANSCRIPT                     │
   │ ┌─────────────────────────────────────┐│
   │ │ [AI]: Thank you for calling...     ││
   │ │ [Patient]: Hi, I need to cancel... ││
   │ │ [AI]: I understand. Let me help... ││
   │ │ [Show More ▼]                      ││
   │ └─────────────────────────────────────┘│
   └─────────────────────────────────────────┘
   ```

4. **Take Action Flow**
   Sarah clicks "Reschedule to Tue 2PM":
   ```
   ┌─────────────────────────────────────────┐
   │ CONFIRM RESCHEDULE              [✕]    │
   ├─────────────────────────────────────────┤
   │ Moving appointment for John Doe        │
   │                                         │
   │ FROM: Nov 26, 2024 @ 2:00 PM           │
   │   TO: Nov 28, 2024 @ 2:00 PM           │
   │                                         │
   │ Doctor: Dr. Rohit Sharma               │
   │ Department: Cardiology                  │
   │                                         │
   │ ☑️ Send WhatsApp confirmation          │
   │ ☑️ Send email confirmation             │
   │ ☐ Call patient to confirm              │
   ├─────────────────────────────────────────┤
   │ [Cancel]              [Confirm Change] │
   └─────────────────────────────────────────┘
   ```

5. **Post-Action State**
   After confirmation:
   - Toast: "✓ Appointment rescheduled. Confirmations sent."
   - Card updates with "Resolved" badge
   - Card moves to bottom of feed or filters out if "Unread Only" is selected
   - Context panel shows action history

---

### Journey 2.2: Real-Time Incoming Interaction

**Persona:** Receptionist actively monitoring the inbox

**Context:** A new Zoice call comes in while Sarah is working

**Flow:**
```
Working on Task → Notification Badge → New Card Animation →
Optional: Auto-expand if High Priority → Take Action
```

**Detailed Experience:**

1. **Passive Notification**
   - Browser notification (if permitted): "New call from John Doe - Frustrated"
   - Tab title updates: "(1) Omni-Inbox | PRM"
   - Inbox badge count increments
   - Subtle sound ping (configurable in settings)

2. **Feed Animation**
   ```
   ┌─────────────────────────────────────────┐
   │ ✨ NEW - Just now                       │
   │ ┌───────────────────────────────────┐  │
   │ │ 🎤 ZOICE CALL                     │  │ ← Slides in from top
   │ │ Mary Johnson • Emergency inquiry  │  │ ← Pulse animation
   │ │ 😰 Anxious • Urgent Question      │  │ ← Red border if urgent
   │ └───────────────────────────────────┘  │
   │                                         │
   │ [Previous cards shift down]             │
   └─────────────────────────────────────────┘
   ```

3. **Auto-Expand for Critical**
   If sentiment is "Frustrated" or "Anxious" AND urgency is "High":
   - Context panel auto-opens
   - Audio cue plays
   - Card highlighted with red border
   - System prompt: "High priority item requires attention"

---

### Journey 2.3: WhatsApp Document Upload Processing

**Persona:** Insurance Coordinator reviewing document uploads

**Context:** Patient sends insurance card photo via WhatsApp

**Flow:**
```
WhatsApp Message Arrives → Document Detected → AI Processing →
Extraction Complete → Review & Confirm → File to Patient Record
```

**Detailed Experience:**

1. **Initial Card**
   ```
   ┌─────────────────────────────────────────┐
   │ 💬 WHATSAPP - 9:15 AM                   │
   │ Jane Smith • Document Upload            │
   │ 📎 1 Image Attached                     │
   │ "Here's my insurance card"              │
   │                                         │
   │ ⏳ Processing document...               │
   └─────────────────────────────────────────┘
   ```

2. **After AI Processing (2-3 seconds)**
   ```
   ┌─────────────────────────────────────────┐
   │ 💬 WHATSAPP - 9:15 AM          [✓ OCR] │
   │ Jane Smith • Insurance Card Uploaded    │
   │                                         │
   │ ┌─────────────────────────────────────┐ │
   │ │ [Thumbnail of Insurance Card]       │ │
   │ │                                     │ │
   │ │ Detected: Aetna PPO                 │ │
   │ │ Member ID: XYZ123456               │ │
   │ │ Group: 98765                        │ │
   │ └─────────────────────────────────────┘ │
   │                                         │
   │ [Review Extraction] [File to Record]    │
   └─────────────────────────────────────────┘
   ```

3. **Review Extraction Modal**
   ```
   ┌─────────────────────────────────────────────────────────┐
   │ REVIEW EXTRACTED DATA                           [✕]    │
   ├─────────────────────────────────────────────────────────┤
   │ ┌───────────────────┬─────────────────────────────────┐│
   │ │                   │ Extracted Fields:               ││
   │ │ [Image Preview]   │                                 ││
   │ │                   │ Insurance Co: [Aetna PPO    ▼] ││
   │ │                   │ Member ID:    [XYZ123456     ] ││
   │ │                   │ Group #:      [98765          ] ││
   │ │                   │ Plan Type:    [PPO           ▼] ││
   │ │                   │ Eff. Date:    [01/01/2024    ] ││
   │ │                   │ Exp. Date:    [12/31/2024    ] ││
   │ └───────────────────┴─────────────────────────────────┘│
   │                                                         │
   │ ⚠️ Low confidence on Group # - please verify          │
   ├─────────────────────────────────────────────────────────┤
   │ [Cancel]                    [Confirm & Save to Record] │
   └─────────────────────────────────────────────────────────┘
   ```

---

### Journey 2.4: Filtering and Search

**Persona:** Department Manager reviewing specific channel activity

**Context:** Dr. Sharma wants to see all Zoice calls from Cardiology patients this week

**Flow:**
```
Open Filter Panel → Select Channel → Select Department →
Select Date Range → Apply → Review Filtered Results
```

**Filter Panel Design:**
```
┌─────────────────────────────────────────────────────────────┐
│ FILTERS                                              [Reset]│
├─────────────────────────────────────────────────────────────┤
│ Channel                                                     │
│ [☑️ Zoice Calls] [☐ WhatsApp] [☐ Email] [☐ SMS] [☐ App]   │
├─────────────────────────────────────────────────────────────┤
│ Department                                                  │
│ [Select Department ▼]                                       │
│ ☑️ Cardiology                                              │
│ ☐ Orthopedics                                              │
│ ☐ General Medicine                                         │
├─────────────────────────────────────────────────────────────┤
│ Date Range                                                  │
│ [This Week ▼]  [Nov 18] → [Nov 25]                         │
├─────────────────────────────────────────────────────────────┤
│ Status                                                      │
│ [☑️ Unread] [☑️ Pending] [☐ Resolved] [☐ Escalated]       │
├─────────────────────────────────────────────────────────────┤
│ Sentiment                                                   │
│ [☐ All] [☐ Positive] [☑️ Negative] [☐ Neutral]            │
├─────────────────────────────────────────────────────────────┤
│ Priority                                                    │
│ [☑️ High] [☑️ Medium] [☐ Low]                              │
├─────────────────────────────────────────────────────────────┤
│ [Apply Filters]                                             │
└─────────────────────────────────────────────────────────────┘
```

**Saved Filters:**
- Users can save filter combinations as presets
- Quick access pills: "My Queue" | "High Priority" | "Unread" | "Today"
- Filters persist in URL for sharing/bookmarking

---

### Journey 2.5: Bulk Actions

**Persona:** Supervisor processing end-of-day cleanup

**Context:** Mark multiple resolved items as complete

**Flow:**
```
Enable Multi-Select → Check Items → Select Bulk Action →
Confirm → Execute → View Results
```

**Multi-Select Mode:**
```
┌─────────────────────────────────────────────────────────────┐
│ ☑️ SELECT MODE                    Selected: 5    [Exit ✕]  │
├─────────────────────────────────────────────────────────────┤
│ [Mark as Read] [Mark Resolved] [Assign To ▼] [Archive]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ☑️ ┌─────────────────────────────────────┐                 │
│    │ 🎤 John Doe - Resolved             │                 │
│    └─────────────────────────────────────┘                 │
│                                                             │
│ ☑️ ┌─────────────────────────────────────┐                 │
│    │ 💬 Jane Smith - Completed          │                 │
│    └─────────────────────────────────────┘                 │
│                                                             │
│ ☐ ┌─────────────────────────────────────┐                 │
│   │ 📧 Bob Wilson - Pending             │                  │
│   └─────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Feed Card Component

**Props:**
```typescript
interface FeedCardProps {
  id: string;
  channel: 'zoice' | 'whatsapp' | 'email' | 'sms' | 'app' | 'system';
  timestamp: Date;
  patient: {
    id: string;
    name: string;
    avatar?: string;
    phone?: string;
  };
  context: string; // Department, visit type, etc.
  sentiment: {
    label: 'positive' | 'negative' | 'neutral' | 'frustrated' | 'anxious';
    score: number; // 0-100
    emoji: string;
  };
  intent: string; // AI-detected intent
  preview: string; // Truncated message
  attachments?: Attachment[];
  priority: 'high' | 'medium' | 'low';
  status: 'unread' | 'read' | 'pending' | 'resolved' | 'escalated';
  suggestedActions: SuggestedAction[];
  isNew?: boolean;
  isSelected?: boolean;
  onSelect?: () => void;
  onAction?: (action: SuggestedAction) => void;
}
```

**Visual States:**
- Default: White background, subtle shadow
- Unread: Left border accent (4px blue)
- Selected: Blue background tint, checkmark
- High Priority: Red left border, subtle red tint
- New: Slide-in animation, pulse glow
- Hover: Elevated shadow, cursor pointer

### Context Panel Component

**Sections:**
1. **Header** - Patient info, close button
2. **Analysis** - Sentiment, intent, urgency metrics
3. **Summary** - AI-generated summary
4. **Suggested Actions** - Clickable action buttons
5. **Media** - Audio player, document previews
6. **Transcript/Content** - Full content with collapse
7. **History** - Previous interactions with this patient

### Real-Time Connection Manager

**WebSocket Events:**
```typescript
// Incoming events
type InboxEvent =
  | { type: 'new_item'; payload: FeedItem }
  | { type: 'item_updated'; payload: Partial<FeedItem> & { id: string } }
  | { type: 'item_resolved'; payload: { id: string; resolvedBy: string } }
  | { type: 'typing'; payload: { conversationId: string; user: string } }
  | { type: 'presence'; payload: { userId: string; status: 'online' | 'away' } };

// Outgoing events
type InboxAction =
  | { type: 'mark_read'; payload: { ids: string[] } }
  | { type: 'subscribe_patient'; payload: { patientId: string } }
  | { type: 'unsubscribe_patient'; payload: { patientId: string } };
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│   Zoice     │  WhatsApp   │    Email    │     SMS     │   App   │
│  Webhooks   │  Webhooks   │   Service   │   Gateway   │  Events │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────┬────┘
       │             │             │             │           │
       └─────────────┴──────┬──────┴─────────────┴───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Omnichannel Inbox   │
                │   Aggregation Layer   │
                │  (Backend Service)    │
                └───────────┬───────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │    AI     │ │   FHIR    │ │  Event    │
       │ Analysis  │ │  Context  │ │  Stream   │
       │ (Sentiment)│ │ (Patient) │ │(WebSocket)│
       └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │    Frontend State     │
                │    (Zustand Store)    │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │    Omni-Inbox UI      │
                │    (React Components) │
                └───────────────────────┘
```

---

## State Management

```typescript
// Zustand Store
interface InboxStore {
  // Data
  items: FeedItem[];
  selectedItemId: string | null;
  filters: InboxFilters;

  // Connection
  isConnected: boolean;
  lastSync: Date | null;

  // UI State
  isMultiSelectMode: boolean;
  selectedIds: Set<string>;
  isFilterPanelOpen: boolean;

  // Actions
  addItem: (item: FeedItem) => void;
  updateItem: (id: string, updates: Partial<FeedItem>) => void;
  selectItem: (id: string | null) => void;
  setFilters: (filters: Partial<InboxFilters>) => void;
  toggleMultiSelect: () => void;
  toggleItemSelection: (id: string) => void;
  bulkAction: (action: BulkAction, ids: string[]) => Promise<void>;
  markAsRead: (ids: string[]) => Promise<void>;
  resolveItem: (id: string, action: string) => Promise<void>;
}
```

---

## Performance Considerations

1. **Virtualized List**
   - Only render visible cards (react-window or @tanstack/virtual)
   - Maintain scroll position during updates
   - Smooth scrolling with momentum

2. **Optimistic Updates**
   - Mark as read instantly, sync in background
   - Show pending state for actions
   - Rollback on failure

3. **Caching Strategy**
   - TanStack Query for API caching
   - Stale-while-revalidate for feed items
   - Local storage for filter preferences

4. **Connection Resilience**
   - Auto-reconnect on disconnect
   - Queue actions during offline
   - Sync on reconnection

---

## Accessibility Requirements

1. **Keyboard Navigation**
   - Arrow keys to move between cards
   - Enter to select/expand card
   - Tab to navigate within context panel
   - Escape to close context panel
   - Space to toggle selection in multi-select mode

2. **Screen Reader Support**
   - Live region for new items announcements
   - Card summaries read as single unit
   - Action buttons properly labeled
   - Status changes announced

3. **Visual Accessibility**
   - High contrast mode support
   - Sentiment colors with icons (not color-only)
   - Focus indicators on all interactive elements

---

## Acceptance Criteria

### AC-1: Feed Display
- [ ] Three-column layout renders correctly on desktop
- [ ] Feed items display with all required information
- [ ] Channel icons and sentiment indicators visible
- [ ] Timestamp displays relative time (e.g., "5 min ago")
- [ ] Feed supports infinite scroll with pagination

### AC-2: Real-Time Updates
- [ ] WebSocket connection established on mount
- [ ] New items appear at top with animation
- [ ] Badge count updates in real-time
- [ ] Connection status indicator visible
- [ ] Auto-reconnect on connection loss

### AC-3: Context Panel
- [ ] Panel slides in when card selected
- [ ] All sections render correctly
- [ ] Audio player functional for Zoice calls
- [ ] Suggested actions execute correctly
- [ ] Close button and Escape key work

### AC-4: Filtering
- [ ] All filter options functional
- [ ] Filters apply without page reload
- [ ] Filter state persists in URL
- [ ] Saved filters work correctly
- [ ] Reset filters clears all selections

### AC-5: Actions
- [ ] Quick actions on cards work
- [ ] Bulk selection mode toggles correctly
- [ ] Bulk actions execute on selected items
- [ ] Success/error feedback displays
- [ ] Undo option for destructive actions

### AC-6: Mobile Responsiveness
- [ ] Single column layout on mobile
- [ ] Context panel as full-screen modal
- [ ] Touch-friendly card interactions
- [ ] Pull-to-refresh functional
- [ ] Bottom sheet for actions

---

## API Contract Examples

### GET /api/v1/prm/omnichannel/inbox

**Request:**
```http
GET /api/v1/prm/omnichannel/inbox?
  channel=zoice,whatsapp&
  status=unread,pending&
  department=cardiology&
  date_from=2024-11-18&
  date_to=2024-11-25&
  limit=20&
  cursor=abc123
```

**Response:**
```json
{
  "items": [
    {
      "id": "inbox_001",
      "channel": "zoice",
      "timestamp": "2024-11-25T07:45:00Z",
      "patient": {
        "id": "patient_123",
        "name": "John Doe",
        "phone": "+15551234567"
      },
      "context": "Cardiology - Dr. Sharma",
      "sentiment": {
        "label": "frustrated",
        "score": 87,
        "emoji": "😤"
      },
      "intent": "reschedule_appointment",
      "preview": "I need to reschedule my appointment tomorrow...",
      "priority": "high",
      "status": "unread",
      "metadata": {
        "call_duration": 272,
        "recording_url": "https://...",
        "transcript_id": "tr_456"
      },
      "suggested_actions": [
        {
          "id": "action_1",
          "type": "reschedule",
          "label": "Reschedule to Tue 2PM",
          "params": { "new_time": "2024-11-28T14:00:00Z" }
        }
      ]
    }
  ],
  "pagination": {
    "next_cursor": "def456",
    "has_more": true,
    "total_count": 47
  }
}
```

---

## Error States

1. **No Items**
   ```
   ┌─────────────────────────────────────────┐
   │                                         │
   │           📭 All caught up!             │
   │                                         │
   │   No items match your current filters.  │
   │   Try adjusting your filters or check   │
   │   back later.                           │
   │                                         │
   │   [Clear Filters]                       │
   └─────────────────────────────────────────┘
   ```

2. **Connection Lost**
   ```
   ┌─────────────────────────────────────────┐
   │ ⚠️ Connection lost. Reconnecting...    │
   │ [Retry Now]                             │
   └─────────────────────────────────────────┘
   ```

3. **Action Failed**
   - Toast: "Failed to reschedule. Please try again."
   - Undo/Retry option
   - Error logged for debugging

---

## Success Metrics

- Time to first interaction: <30 seconds after login
- Average items processed per hour: 25% improvement
- Missed high-priority items: <1%
- User satisfaction with inbox: >4.5/5 stars
- Real-time latency: <500ms for new items

---

**Document Owner:** Frontend Product Team
**Last Updated:** November 25, 2024
**Review Cycle:** Every Sprint
