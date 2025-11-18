# Phase 6: Frontend Planning - Agent-Native PRM Dashboard

**Date:** November 19, 2024
**Status:** Planning Phase
**Paradigm:** AI-First, Agent-Native, Voice-Enabled

---

## 🎯 Vision Statement

Build a **revolutionary, agent-native PRM dashboard** where the AI assistant is the **primary interface** for all operations. Staff interact using natural language (text or voice), and the AI orchestrates a suite of specialized agents and tools to execute complex workflows with minimal clicks.

**Core Principle:** *"Talk to your system like you'd talk to an expert assistant"*

---

## 🌟 Design Philosophy: Agent-Native UX

### What Makes This Different

**Traditional CRM:**
- Click through menus to find features
- Fill out complex forms manually
- Navigate between multiple screens
- Remember where everything is

**Agent-Native PRM:**
- **Speak or type what you want**: "Schedule callback for arunank tomorrow at 2pm"
- **AI executes via specialized agents**: Validates patient, checks slots, books, sends confirmation
- **One-click confirmation**: Review and approve in a beautiful UI
- **Zero navigation required**: AI brings the interface to you

### Inspired by Best-in-Class Systems

| System | Best Pattern | How We Apply It |
|--------|-------------|-----------------|
| **Salesforce Lightning** | Command Palette (Cmd+K) | AI Command Bar - always accessible |
| **HubSpot** | Unified Inbox | All communications + AI chat in one timeline |
| **Linear** | Keyboard-first, fast | Keyboard shortcuts + voice shortcuts |
| **Intercom** | Context-aware AI | AI knows what page you're on, suggests actions |
| **Zendesk** | Macros for common actions | AI learns patterns, creates shortcuts |
| **Superhuman** | Speed, keyboard shortcuts | Ultra-fast, minimal clicks |
| **Notion** | Slash commands | AI commands like `/schedule`, `/book`, `/send` |

---

## 🏗️ System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     PRM Dashboard Frontend                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           AI Assistant (Primary Interface)            │  │
│  │  - Text Chat                                          │  │
│  │  - Voice Input/Output                                 │  │
│  │  - Command Parser                                     │  │
│  │  - Action Orchestrator                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓↑                                 │
│  ┌─────────────────┬──────────────────┬─────────────────┐  │
│  │  Agent Suite    │  Traditional UI  │   Tool System   │  │
│  │  - Appointment  │  - Patient 360   │   - API Calls   │  │
│  │  - Journey      │  - Calendar      │   - DB Queries  │  │
│  │  - Billing      │  - Timeline      │   - Workflows   │  │
│  │  - Communication│  - Forms         │   - Actions     │  │
│  └─────────────────┴──────────────────┴─────────────────┘  │
│                           ↓↑                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PRM Backend API (16 Modules)             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Assistant Architecture

### 1. Core Assistant Components

#### A. Conversation Platform Integration

**Reuse Healthcare Conversation Platform:**

```typescript
import { ConversationWidget, useConversation } from '@healthcare-conversation/ui';

// Integrate with PRM-specific schema
const prmActionSchema = {
  type: "object",
  properties: {
    intent: {
      enum: [
        "book_appointment", "schedule_callback", "send_message",
        "create_journey", "update_patient", "fetch_status",
        "complete_billing", "assign_ticket", "send_reminder"
      ]
    },
    entities: { /* extracted parameters */ },
    confidence: { type: "number" }
  }
};

function PRMAssistant() {
  return (
    <ConversationWidget
      apiUrl={CONVERSATION_API_URL}
      wsUrl={CONVERSATION_WS_URL}
      formSchema={prmActionSchema}
      formType="prm_action"
      userId={currentUser.id}
      mode="mixed" // text + voice
      onExtractionComplete={executeAction}
    />
  );
}
```

#### B. AI Command Bar (Cmd+K)

**Always-accessible command interface:**

```typescript
// Universal command palette
<CommandBar
  trigger={["cmd+k", "ctrl+k", "/"]}
  placeholder="What would you like to do? (Try: 'schedule appointment for...')"
  recentCommands={userRecentCommands}
  suggestions={contextualSuggestions}
  onExecute={async (command) => {
    // Parse natural language → structured action
    const action = await parseCommand(command);
    // Execute via appropriate agent
    await executeWithAgent(action);
  }}
/>
```

**Example Commands:**
```
"schedule appointment for patient 9844111173 with dr rajiv tomorrow 10am"
"send whatsapp reminder to all patients with appointments today"
"show me patients who missed appointments this week"
"create callback for arunank at 2pm tomorrow"
"complete billing for patient sharma"
"update patient phone number to 9876543210"
```

#### C. Voice Interface

**Hands-free operation using existing voice pipeline:**

```typescript
import { useLiveKit } from '@healthcare-conversation/ui';

function VoiceControl() {
  const {
    isConnected,
    startVoice,
    stopVoice,
    transcript
  } = useLiveKit({
    apiUrl: LIVEKIT_URL,
    onTranscript: (text) => {
      // Parse and execute
      executeNaturalLanguageCommand(text);
    }
  });

  return (
    <VoiceButton
      isActive={isConnected}
      onPress={startVoice}
      transcript={transcript}
    />
  );
}
```

**Voice Commands:**
```
"Hey PRM, schedule callback for Arun Kumar tomorrow at 2pm"
"Show me appointments for Dr. Sharma today"
"Send reminder to patient 9844111173"
"Complete billing for last patient"
```

---

### 2. Agent System Architecture

#### A. Specialized Domain Agents

Each agent is a specialized LLM-powered component that handles specific domain operations:

```typescript
// Agent Registry
const agents = {
  // Phase 1 Agents
  appointmentAgent: new AppointmentAgent({
    tools: [
      "checkAvailability",
      "bookSlot",
      "reschedule",
      "cancel",
      "sendReminder",
      "findSlots"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You are an expert appointment scheduler..."
  }),

  journeyAgent: new JourneyAgent({
    tools: [
      "createInstance",
      "advanceStage",
      "pauseJourney",
      "getStatus",
      "listActive"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You orchestrate patient care journeys..."
  }),

  communicationAgent: new CommunicationAgent({
    tools: [
      "sendWhatsApp",
      "sendSMS",
      "sendEmail",
      "getHistory",
      "bulkSend"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You handle all patient communications..."
  }),

  billingAgent: new BillingAgent({
    tools: [
      "completeBilling",
      "getInvoice",
      "sendReceipt",
      "processPayment"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You manage billing and payments..."
  }),

  // Phase 2 Agents
  patientAgent: new PatientAgent({
    tools: [
      "search",
      "create",
      "update",
      "get360View",
      "getHistory"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You manage patient records..."
  }),

  ticketAgent: new TicketAgent({
    tools: [
      "create",
      "assign",
      "resolve",
      "escalate",
      "getStatus"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You handle support tickets..."
  }),

  // Phase 3 Agents
  vectorAgent: new VectorAgent({
    tools: [
      "semanticSearch",
      "findSimilar",
      "recommendations"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You provide intelligent search..."
  }),

  intakeAgent: new IntakeAgent({
    tools: [
      "processVoiceCall",
      "extractInfo",
      "fillForm",
      "validateData"
    ],
    llm: "gpt-4-turbo",
    systemPrompt: "You handle patient intake..."
  })
};
```

#### B. Agent Base Class

```typescript
abstract class BaseAgent {
  constructor(
    protected tools: Tool[],
    protected llm: LLMClient,
    protected systemPrompt: string
  ) {}

  async execute(userIntent: string, context: Context): Promise<AgentResult> {
    // 1. Understand intent
    const understanding = await this.llm.analyze(userIntent, context);

    // 2. Plan execution
    const plan = await this.planExecution(understanding);

    // 3. Execute tools
    const results = await this.executeTools(plan);

    // 4. Format response
    return this.formatResponse(results);
  }

  protected abstract planExecution(understanding: Understanding): Promise<ExecutionPlan>;
  protected abstract executeTools(plan: ExecutionPlan): Promise<ToolResults>;
}
```

#### C. Tool System

**Tools are atomic backend operations:**

```typescript
// Tool definitions
const tools: Tool[] = [
  {
    name: "check_appointment_availability",
    description: "Check available appointment slots for a practitioner",
    parameters: {
      practitioner_id: "string",
      speciality: "string",
      date_range: "object",
      location_id: "string?"
    },
    execute: async (params) => {
      const response = await api.get('/api/v1/prm/appointments/slots', { params });
      return response.data;
    }
  },

  {
    name: "book_appointment",
    description: "Book an appointment slot",
    parameters: {
      patient_id: "string",
      practitioner_id: "string",
      slot_id: "string",
      appointment_type: "string",
      notes: "string?"
    },
    execute: async (params) => {
      const response = await api.post('/api/v1/prm/appointments', params);
      return response.data;
    }
  },

  {
    name: "send_whatsapp_message",
    description: "Send WhatsApp message to patient",
    parameters: {
      patient_id: "string",
      template_id: "string?",
      message: "string",
      media_url: "string?"
    },
    execute: async (params) => {
      const response = await api.post('/api/v1/prm/communications', {
        ...params,
        channel: 'whatsapp'
      });
      return response.data;
    }
  },

  {
    name: "create_journey_instance",
    description: "Start a patient journey",
    parameters: {
      patient_id: "string",
      journey_definition_id: "string",
      context: "object?"
    },
    execute: async (params) => {
      const response = await api.post('/api/v1/prm/instances', params);
      return response.data;
    }
  },

  {
    name: "search_patients",
    description: "Search for patients by phone, name, or MRN",
    parameters: {
      query: "string",
      search_type: "enum['phone', 'name', 'mrn']"
    },
    execute: async (params) => {
      const response = await api.get('/api/v1/prm/patients/search', { params });
      return response.data;
    }
  },

  {
    name: "get_patient_360",
    description: "Get complete patient profile",
    parameters: {
      patient_id: "string"
    },
    execute: async (params) => {
      const response = await api.get(`/api/v1/prm/patients/${params.patient_id}/360`);
      return response.data;
    }
  },

  {
    name: "complete_billing",
    description: "Mark billing complete for patient",
    parameters: {
      patient_id: "string",
      amount: "number",
      payment_method: "string",
      notes: "string?"
    },
    execute: async (params) => {
      const response = await api.post('/api/v1/prm/billing/complete', params);
      return response.data;
    }
  }
];
```

---

### 3. Natural Language Processing Flow

```
User Input (Text/Voice)
        ↓
┌──────────────────┐
│  Intent Parser   │  ← LLM extracts intent + entities
└──────────────────┘
        ↓
┌──────────────────┐
│  Agent Router    │  ← Routes to appropriate agent
└──────────────────┘
        ↓
┌──────────────────┐
│ Domain Agent     │  ← Specialized agent (Appointment, Journey, etc.)
└──────────────────┘
        ↓
┌──────────────────┐
│ Tool Executor    │  ← Calls backend APIs via tools
└──────────────────┘
        ↓
┌──────────────────┐
│ Response Formatter│ ← Formats result for user
└──────────────────┘
        ↓
┌──────────────────┐
│ Confirmation UI  │  ← Shows action for approval
└──────────────────┘
        ↓
   User Approves
        ↓
┌──────────────────┐
│ Action Executed  │
└──────────────────┘
        ↓
┌──────────────────┐
│ Success Feedback │
└──────────────────┘
```

---

### 4. Example: Multi-Step Agent Workflow

**User Command:**
*"Schedule an appointment of arunank with dr. rajiv sharma from orthopaedics for tomorrow 10am"*

**Step-by-Step Execution:**

```typescript
// 1. Intent Parsing
const parsedIntent = await intentParser.parse(userCommand);
/* Result:
{
  intent: "book_appointment",
  entities: {
    patient_identifier: "arunank",
    practitioner_name: "dr. rajiv sharma",
    speciality: "orthopaedics",
    date: "2024-11-20",
    time: "10:00",
    duration: null
  },
  confidence: 0.95
}
*/

// 2. Route to Appointment Agent
const agent = agentRouter.route(parsedIntent.intent);
// Returns: appointmentAgent

// 3. Agent Orchestrates Sub-Tasks
const result = await agent.execute({
  async resolvePatient() {
    // Tool: search_patients
    const patients = await tools.search_patients({
      query: "arunank",
      search_type: "name"
    });

    if (patients.length > 1) {
      // Clarification needed
      return await askClarification("Multiple patients found", patients);
    }
    return patients[0];
  },

  async resolvePractitioner() {
    // Tool: search_practitioners
    const practitioners = await tools.search_practitioners({
      name: "rajiv sharma",
      speciality: "orthopaedics"
    });
    return practitioners[0];
  },

  async checkAvailability() {
    // Tool: check_appointment_availability
    const slots = await tools.check_appointment_availability({
      practitioner_id: practitioner.id,
      date_range: { start: "2024-11-20 10:00", end: "2024-11-20 10:30" }
    });
    return slots;
  },

  async bookAppointment() {
    // Tool: book_appointment
    const appointment = await tools.book_appointment({
      patient_id: patient.id,
      practitioner_id: practitioner.id,
      slot_id: availableSlots[0].id,
      appointment_type: "consultation"
    });
    return appointment;
  },

  async sendConfirmation() {
    // Tool: send_whatsapp_message
    await tools.send_whatsapp_message({
      patient_id: patient.id,
      template_id: "appointment_confirmation",
      message: `Your appointment with ${practitioner.name} is confirmed for Nov 20 at 10:00 AM`
    });
  }
});

// 4. Show Confirmation UI
showConfirmationDialog({
  title: "Appointment Booking",
  summary: `
    Patient: ${patient.name} (${patient.phone})
    Practitioner: ${practitioner.name} - Orthopaedics
    Date & Time: Nov 20, 2024 at 10:00 AM
    Location: ${slot.location.name}
  `,
  actions: [
    { label: "Confirm & Book", action: () => finalizeBooking() },
    { label: "Modify", action: () => showEditForm() },
    { label: "Cancel", action: () => cancelAction() }
  ]
});

// 5. User Confirms → Execute
await finalizeBooking();

// 6. Success Feedback
showToast({
  type: "success",
  message: "Appointment booked successfully! Confirmation sent via WhatsApp.",
  actions: [
    { label: "View Appointment", link: `/appointments/${appointment.id}` },
    { label: "View Patient", link: `/patients/${patient.id}` }
  ]
});
```

---

## 📐 UI/UX Design

### 1. Layout Architecture

```
┌────────────────────────────────────────────────────────────────┐
│ ┌──────────┐  Header + Global Command Bar (Cmd+K)      [👤][⚙]│
│ └──────────┘                                                    │
├────────────────────────────────────────────────────────────────┤
│ │          │                                          │         │
│ │          │                                          │   AI    │
│ │          │                                          │Assistant│
│ │ Sidebar  │      Main Content Area                  │ Panel   │
│ │          │                                          │         │
│ │          │      (Context-Aware Views)               │ [Chat]  │
│ │ [Nav]    │                                          │ [Voice] │
│ │ [Quick   │      ┌─────────────────────────┐        │ [Tools] │
│ │  Actions]│      │  Patient 360° View      │        │         │
│ │          │      │  or                     │        │ Recent  │
│ │          │      │  Calendar View          │        │ Actions │
│ │          │      │  or                     │        │         │
│ │          │      │  Journey Timeline       │        │ Suggest │
│ │          │      │  or                     │        │ ions    │
│ │          │      │  Dashboard Metrics      │        │         │
│ │          │      └─────────────────────────┘        │         │
│ │          │                                          │         │
└─┴──────────┴──────────────────────────────────────────┴─────────┘
```

### 2. AI Assistant Panel (Always Visible)

**Position:** Right sidebar, always accessible
**Width:** 400px (collapsible to 60px icon-only mode)
**Components:**

```typescript
<AIAssistantPanel>
  {/* Voice/Text Toggle */}
  <ModeSelector mode={mode} onChange={setMode} />

  {/* Conversation Area */}
  <ConversationArea>
    {messages.map(msg => (
      <Message
        key={msg.id}
        role={msg.role}
        content={msg.content}
        actions={msg.actions} // Executable buttons
        timestamp={msg.timestamp}
      />
    ))}
  </ConversationArea>

  {/* Input Area */}
  <InputArea>
    {mode === 'voice' ? (
      <VoiceInput onTranscript={handleCommand} />
    ) : (
      <TextInput
        placeholder="Try: 'schedule callback for arunank tomorrow 2pm'"
        onSubmit={handleCommand}
        suggestions={contextualSuggestions}
      />
    )}
  </InputArea>

  {/* Quick Actions (Context-Aware) */}
  <QuickActions>
    {suggestedActions.map(action => (
      <QuickActionButton
        key={action.id}
        icon={action.icon}
        label={action.label}
        onClick={() => executeAction(action)}
      />
    ))}
  </QuickActions>

  {/* Recent Actions Log */}
  <RecentActions>
    {recentActions.map(action => (
      <ActionItem
        key={action.id}
        type={action.type}
        summary={action.summary}
        timestamp={action.timestamp}
        onUndo={() => undoAction(action.id)}
      />
    ))}
  </RecentActions>
</AIAssistantPanel>
```

### 3. Confirmation UI Pattern

**When AI executes an action, show beautiful confirmation:**

```typescript
<ConfirmationCard>
  <Header>
    <Icon type={actionType} />
    <Title>{actionTitle}</Title>
  </Header>

  <Summary>
    <KeyValue label="Patient" value="Arun Kumar (9844111173)" />
    <KeyValue label="Doctor" value="Dr. Rajiv Sharma - Orthopaedics" />
    <KeyValue label="Date & Time" value="Nov 20, 2024 at 10:00 AM" />
    <KeyValue label="Location" value="Main Clinic, Room 203" />
  </Summary>

  <Actions>
    <Button variant="primary" onClick={confirm}>
      Confirm & Book
    </Button>
    <Button variant="secondary" onClick={modify}>
      Modify
    </Button>
    <Button variant="ghost" onClick={cancel}>
      Cancel
    </Button>
  </Actions>

  <ConfidenceIndicator>
    <Badge color="green">95% Confidence</Badge>
  </ConfidenceIndicator>
</ConfirmationCard>
```

---

### 4. Contextual Suggestions

**AI suggests actions based on current context:**

```typescript
// On Patient 360 page
const contextualSuggestions = [
  {
    icon: "📅",
    label: "Schedule Appointment",
    command: "schedule appointment for this patient"
  },
  {
    icon: "💬",
    label: "Send Message",
    command: "send whatsapp message to this patient"
  },
  {
    icon: "🗺️",
    label: "Start Journey",
    command: "start onboarding journey for this patient"
  },
  {
    icon: "💰",
    label: "Complete Billing",
    command: "complete billing for this patient"
  }
];

// On Appointments Calendar
const contextualSuggestions = [
  {
    icon: "📅",
    label: "Book New Appointment",
    command: "book new appointment"
  },
  {
    icon: "🔔",
    label: "Send Today's Reminders",
    command: "send reminders to all patients with appointments today"
  },
  {
    icon: "📊",
    label: "View No-Shows",
    command: "show patients who missed appointments this week"
  }
];
```

---

## 🎨 Traditional UI Components (Hybrid Mode)

While AI is primary, traditional UI is available for:
1. **Visual browsing** (calendar, timeline)
2. **Batch operations** (bulk actions on table)
3. **Complex forms** (detailed configuration)
4. **Analytics** (charts, dashboards)

### Key Pages

#### 1. Dashboard Home

```
┌─────────────────────────────────────────────────────────┐
│  Dashboard - Today's Overview                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Today's  │  │ Active   │  │ Pending  │  │ Messages││
│  │ Appts    │  │ Journeys │  │ Tickets  │  │ Sent    ││
│  │   24     │  │    156   │  │    8     │  │   142   ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                                                          │
│  Recent Activity Feed                    Upcoming       │
│  ┌────────────────────────────┐  ┌──────────────────┐  │
│  │ 10:30 - Appointment booked │  │ 11:00 - Rajiv S. │  │
│  │ 10:25 - Journey completed  │  │ 11:30 - Priya K. │  │
│  │ 10:20 - Ticket resolved    │  │ 14:00 - Arun S.  │  │
│  │ 10:15 - Patient registered │  │ 15:00 - Sarah M. │  │
│  └────────────────────────────┘  └──────────────────┘  │
│                                                          │
│  Journey Status Chart         Communication Analytics   │
│  ┌────────────────────────────┐  ┌──────────────────┐  │
│  │    [Donut Chart]           │  │  [Bar Chart]     │  │
│  │  - Active: 60%             │  │  WhatsApp: 80    │  │
│  │  - Paused: 25%             │  │  SMS: 40         │  │
│  │  - Completed: 15%          │  │  Email: 22       │  │
│  └────────────────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**AI Integration:**
- Quick actions in dashboard: "Show me high-priority items"
- Voice: "What do I need to focus on today?"
- Proactive alerts: "3 appointments need confirmation calls"

---

#### 2. Patient 360° View

```
┌─────────────────────────────────────────────────────────┐
│  Patient: Arun Kumar                              [Edit]│
│  MRN: MR001234 | Phone: 9844111173 | Age: 45      [⋮]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Overview │  │ Journeys │  │  Appts   │  │  Comms  ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                                                          │
│  Demographics              Active Journeys               │
│  ┌──────────────────┐     ┌──────────────────────────┐  │
│  │ Name: Arun Kumar │     │ Post-Surgery Recovery    │  │
│  │ DOB: 1979-05-15  │     │ Stage 3/5 - Follow-up    │  │
│  │ Gender: Male     │     │ Progress: ▓▓▓▓░░ 60%     │  │
│  │ Blood: O+        │     └──────────────────────────┘  │
│  └──────────────────┘     ┌──────────────────────────┐  │
│                           │ Pre-Op Preparation       │  │
│  Contact Info             │ Stage 2/4 - Tests        │  │
│  ┌──────────────────┐     │ Progress: ▓▓░░░░ 40%     │  │
│  │ Phone: 98441...  │     └──────────────────────────┘  │
│  │ Email: arun@...  │                                   │
│  │ Address: ...     │     Upcoming Appointments         │
│  └──────────────────┘     ┌──────────────────────────┐  │
│                           │ Nov 20, 10:00 AM         │  │
│  Recent Activity          │ Dr. Rajiv - Orthopaedics │  │
│  ┌──────────────────┐     └──────────────────────────┘  │
│  │ Nov 18: Message  │     ┌──────────────────────────┐  │
│  │ Nov 15: Appt     │     │ Nov 25, 2:00 PM          │  │
│  │ Nov 10: Journey  │     │ Dr. Priya - Cardiology   │  │
│  └──────────────────┘     └──────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**AI Integration:**
- Command: "Schedule follow-up for this patient next week"
- Voice: "Send appointment reminder to this patient"
- Proactive: "This patient has a journey stage due tomorrow"

---

#### 3. Appointment Calendar

```
┌─────────────────────────────────────────────────────────┐
│  Appointments Calendar               [Week] [Month] [Day]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  < Nov 19, 2024 >         Filter: All Practitioners     │
│                                                          │
│  Time   | Dr. Rajiv (Ortho) | Dr. Priya (Cardio)       │
│  ───────┼───────────────────┼──────────────────────    │
│  09:00  │ ┌───────────────┐ │ ┌───────────────┐        │
│  09:30  │ │ Arun Kumar    │ │ │ Sarah Miller  │        │
│  10:00  │ │ Consultation  │ │ │ Follow-up     │        │
│  10:30  │ └───────────────┘ │ └───────────────┘        │
│  11:00  │ ┌───────────────┐ │ [Available]              │
│  11:30  │ │ Priya Sharma  │ │                          │
│  12:00  │ │ Check-up      │ │                          │
│  12:30  │ └───────────────┘ │                          │
│  13:00  │ [LUNCH BREAK]     │ [LUNCH BREAK]            │
│  14:00  │ [Available]       │ ┌───────────────┐        │
│  14:30  │                   │ │ John Doe      │        │
│  15:00  │                   │ │ Procedure     │        │
│  15:30  │                   │ └───────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**AI Integration:**
- Command: "Find next available slot with Dr. Rajiv"
- Voice: "Book appointment for patient Arun at 2pm"
- Drag appointment → AI: "Confirm reschedule? Send notification?"

---

#### 4. Communication Timeline

```
┌─────────────────────────────────────────────────────────┐
│  Communications                  [All] [WhatsApp] [SMS] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Search: [                     ]  Filter: Today ▼       │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 10:30 AM - WhatsApp → Arun Kumar (9844111173)     │ │
│  │ "Your appointment with Dr. Rajiv is confirmed..."  │ │
│  │ Status: Delivered ✓✓                               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 10:25 AM - SMS → Priya Sharma (9876543210)        │ │
│  │ "Reminder: Appointment tomorrow at 2 PM"           │ │
│  │ Status: Sent ✓                                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 09:45 AM - Email → sarah@email.com                │ │
│  │ "Lab results are ready for pickup"                 │ │
│  │ Status: Read 👁                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**AI Integration:**
- Command: "Send reminder to all patients with appointments tomorrow"
- Voice: "Show messages sent to patient 9844111173"
- Bulk action: Select multiple → "Send follow-up message to selected patients"

---

## 🛠️ Technology Stack

### Frontend Framework
- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **React 18+** with Server Components

### UI Framework
- **Shadcn/ui** - Beautiful, accessible components
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Unstyled, accessible primitives
- **Framer Motion** - Smooth animations

### State Management
- **React Query (TanStack Query)** - Server state, caching
- **Zustand** - Client state, UI state
- **WebSocket** - Real-time updates

### AI Integration
- **Healthcare Conversation Platform** (existing)
  - Voice pipeline (LiveKit, Whisper, ElevenLabs)
  - Conversation core (NestJS, MongoDB)
  - Conversation UI (React components)
- **OpenAI GPT-4 Turbo** - Intent parsing, agent orchestration
- **LangChain** - Agent framework, tool calling

### Data Visualization
- **Recharts** - Charts and graphs
- **React Flow** - Journey visualization, flowcharts

### Real-time
- **Socket.io** or **WebSocket** - Live updates
- **Server-Sent Events** - Streaming responses

---

## 🔄 Data Flow Architecture

```
┌────────────────────────────────────────────────────┐
│                 User Interface                      │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ AI Assistant │  │ Traditional │  │  Command  │ │
│  │  (Primary)   │  │     UI      │  │  Palette  │ │
│  └──────────────┘  └─────────────┘  └───────────┘ │
└─────────────┬──────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│          Frontend State Management                  │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ React Query  │  │   Zustand   │  │ WebSocket │  │
│  │ (Server)     │  │   (Client)  │  │  (Live)   │  │
│  └──────────────┘  └─────────────┘  └───────────┘  │
└─────────────┬───────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│              AI Orchestration Layer                 │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ Intent Parser│  │Agent Router │  │  Tool     │  │
│  │   (LLM)      │  │             │  │ Executor  │  │
│  └──────────────┘  └─────────────┘  └───────────┘  │
└─────────────┬───────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│           Backend API (PRM Service)                 │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┐    │
│  │J│C│T│W│A│P│M│N│V│I│... 16 modules          │    │
│  └────┴────┴────┴────┴────┴────┴────┴────┴────┘    │
└─────────────┬───────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│                  Database Layer                     │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ PostgreSQL   │  │    Redis    │  │  Vector   │  │
│  │ (Persistent) │  │   (Cache)   │  │   (RAG)   │  │
│  └──────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Project Structure

```
prm-frontend/
├── app/                          # Next.js app directory
│   ├── (auth)/                   # Authentication routes
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/              # Main dashboard
│   │   ├── layout.tsx            # Dashboard layout
│   │   ├── page.tsx              # Dashboard home
│   │   ├── patients/
│   │   │   ├── page.tsx          # Patient list
│   │   │   ├── [id]/             # Patient 360 view
│   │   │   └── new/              # Create patient
│   │   ├── appointments/
│   │   │   ├── page.tsx          # Calendar view
│   │   │   ├── [id]/             # Appointment detail
│   │   │   └── slots/            # Slot management
│   │   ├── journeys/
│   │   │   ├── page.tsx          # Journey definitions
│   │   │   ├── [id]/             # Journey detail
│   │   │   ├── builder/          # Journey builder
│   │   │   └── instances/        # Active instances
│   │   ├── communications/
│   │   │   ├── page.tsx          # Communication timeline
│   │   │   └── templates/        # Message templates
│   │   ├── tickets/
│   │   │   ├── page.tsx          # Ticket list
│   │   │   └── [id]/             # Ticket detail
│   │   └── settings/
│   └── api/                      # API routes (if needed)
│
├── components/                   # React components
│   ├── ui/                       # Shadcn/ui components
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── ai-assistant/             # AI assistant components
│   │   ├── AIPanel.tsx           # Main AI panel
│   │   ├── ChatInterface.tsx    # Text chat UI
│   │   ├── VoiceControl.tsx     # Voice input
│   │   ├── CommandBar.tsx       # Cmd+K interface
│   │   ├── ConfirmationCard.tsx # Action confirmation
│   │   ├── AgentStatus.tsx      # Agent execution status
│   │   └── QuickActions.tsx     # Contextual actions
│   ├── patients/                 # Patient components
│   │   ├── PatientCard.tsx
│   │   ├── Patient360.tsx
│   │   └── PatientList.tsx
│   ├── appointments/             # Appointment components
│   │   ├── Calendar.tsx
│   │   ├── AppointmentCard.tsx
│   │   └── SlotPicker.tsx
│   ├── journeys/                 # Journey components
│   │   ├── JourneyBuilder.tsx
│   │   ├── StageCard.tsx
│   │   └── ProgressBar.tsx
│   ├── communications/           # Communication components
│   │   ├── Timeline.tsx
│   │   ├── MessageComposer.tsx
│   │   └── TemplateSelector.tsx
│   └── common/                   # Common components
│       ├── DataTable.tsx
│       ├── SearchBar.tsx
│       ├── FilterPanel.tsx
│       └── Charts/
│
├── lib/                          # Core utilities
│   ├── ai/                       # AI/Agent logic
│   │   ├── agents/               # Specialized agents
│   │   │   ├── BaseAgent.ts     # Base agent class
│   │   │   ├── AppointmentAgent.ts
│   │   │   ├── JourneyAgent.ts
│   │   │   ├── CommunicationAgent.ts
│   │   │   ├── BillingAgent.ts
│   │   │   ├── PatientAgent.ts
│   │   │   └── TicketAgent.ts
│   │   ├── tools/                # Tool definitions
│   │   │   ├── appointment-tools.ts
│   │   │   ├── patient-tools.ts
│   │   │   ├── journey-tools.ts
│   │   │   └── communication-tools.ts
│   │   ├── intent-parser.ts     # LLM-based intent parsing
│   │   ├── agent-router.ts      # Routes intent to agent
│   │   └── orchestrator.ts      # Main orchestration logic
│   ├── api/                      # API client
│   │   ├── client.ts             # Axios instance
│   │   ├── patients.ts
│   │   ├── appointments.ts
│   │   ├── journeys.ts
│   │   ├── communications.ts
│   │   └── tickets.ts
│   ├── hooks/                    # Custom React hooks
│   │   ├── usePatients.ts
│   │   ├── useAppointments.ts
│   │   ├── useJourneys.ts
│   │   ├── useAIAssistant.ts    # AI assistant hook
│   │   ├── useRealtime.ts       # WebSocket hook
│   │   └── useAgents.ts         # Agent orchestration hook
│   ├── utils/                    # Utility functions
│   │   ├── date.ts
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   └── cn.ts                 # Tailwind class merging
│   ├── types/                    # TypeScript types
│   │   ├── patient.ts
│   │   ├── appointment.ts
│   │   ├── journey.ts
│   │   ├── agent.ts
│   │   └── api.ts
│   └── store/                    # Zustand stores
│       ├── ui-store.ts           # UI state
│       ├── user-store.ts         # User preferences
│       └── assistant-store.ts    # AI assistant state
│
├── integrations/                 # External integrations
│   ├── conversation-platform/   # Healthcare conversation platform
│   │   ├── adapters/            # Adapters for PRM
│   │   ├── schemas/             # PRM-specific schemas
│   │   └── config.ts            # Configuration
│   └── backend/                 # PRM backend integration
│       ├── websocket.ts         # WebSocket client
│       └── events.ts            # Event handlers
│
├── public/                       # Static assets
│   ├── icons/
│   └── images/
│
├── styles/                       # Global styles
│   └── globals.css
│
├── .env.local                    # Environment variables
├── next.config.js                # Next.js configuration
├── tailwind.config.ts            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
└── package.json                  # Dependencies
```

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
- [ ] **Project Setup**
  - Initialize Next.js 14 project
  - Set up TypeScript, Tailwind, Shadcn/ui
  - Configure development environment

- [ ] **AI Infrastructure**
  - Integrate healthcare conversation platform
  - Set up intent parser (LLM integration)
  - Create base agent class
  - Implement tool system framework

- [ ] **Core Components**
  - Layout components (Sidebar, Header)
  - AI Assistant panel
  - Command Bar (Cmd+K)
  - Voice control component

- [ ] **Backend Integration**
  - API client setup
  - WebSocket integration
  - React Query configuration

---

### Phase 2: Core Agents (Weeks 4-7)
- [ ] **Appointment Agent**
  - Implement appointment tools
  - Create appointment agent logic
  - Build confirmation UI
  - Test: "Schedule appointment for..."

- [ ] **Patient Agent**
  - Implement patient search
  - Create patient CRUD tools
  - Build patient 360 view
  - Test: "Find patient with phone..."

- [ ] **Communication Agent**
  - Implement messaging tools
  - Create template system
  - Build communication timeline
  - Test: "Send WhatsApp to..."

- [ ] **Journey Agent**
  - Implement journey tools
  - Create instance management
  - Build journey visualization
  - Test: "Start onboarding journey for..."

---

### Phase 3: Traditional UI Views (Weeks 8-11)
- [ ] **Dashboard Home**
  - Metrics cards
  - Activity feed
  - Quick actions
  - Charts and graphs

- [ ] **Patient 360° View**
  - Demographics section
  - Active journeys
  - Appointments
  - Communication timeline
  - Ticket history

- [ ] **Appointment Calendar**
  - Calendar view (day/week/month)
  - Slot management
  - Drag-and-drop
  - Filter by practitioner

- [ ] **Communication Center**
  - Unified timeline
  - Message composer
  - Template library
  - Bulk messaging

---

### Phase 4: Advanced Agents (Weeks 12-15)
- [ ] **Billing Agent**
  - Complete billing tool
  - Invoice generation
  - Payment processing
  - Receipt sending

- [ ] **Ticket Agent**
  - Ticket creation
  - Assignment logic
  - Resolution workflow
  - Escalation handling

- [ ] **Vector Agent** (RAG)
  - Semantic search
  - Recommendations
  - Similar patients
  - Knowledge base queries

- [ ] **Intake Agent**
  - Voice call processing
  - Form auto-fill
  - Data validation
  - Multi-step conversations

---

### Phase 5: Polish & Optimization (Weeks 16-19)
- [ ] **UX Enhancements**
  - Keyboard shortcuts
  - Loading states
  - Error handling
  - Empty states
  - Onboarding tour

- [ ] **Performance**
  - Code splitting
  - Lazy loading
  - Image optimization
  - Bundle size reduction
  - React Query caching

- [ ] **Accessibility**
  - WCAG 2.1 AA compliance
  - Keyboard navigation
  - Screen reader support
  - Color contrast
  - Focus management

- [ ] **Mobile Responsiveness**
  - Mobile layouts
  - Touch gestures
  - Bottom navigation
  - Swipe actions

---

### Phase 6: Testing & Deployment (Weeks 20-22)
- [ ] **Testing**
  - Unit tests (Vitest)
  - Integration tests
  - E2E tests (Playwright)
  - Accessibility tests
  - Performance testing

- [ ] **Documentation**
  - User manual
  - API documentation
  - Video tutorials
  - FAQ
  - Troubleshooting guide

- [ ] **Deployment**
  - Staging deployment
  - UAT with real users
  - Production deployment
  - Monitoring setup
  - Analytics integration

---

## 🎯 Success Metrics

### User Experience Goals
- [ ] **Intuitive**: 90% of users can complete common tasks without training
- [ ] **Fast**: < 1s page load, < 200ms interaction response
- [ ] **Accessible**: WCAG 2.1 AA compliance, keyboard + screen reader support
- [ ] **Mobile-friendly**: Works seamlessly on tablets and phones

### AI Performance Goals
- [ ] **Intent Accuracy**: 95%+ intent recognition accuracy
- [ ] **Action Success**: 90%+ successful action execution
- [ ] **Response Time**: < 2s for AI response
- [ ] **User Satisfaction**: 4.5+ / 5.0 rating

### Technical Goals
- [ ] **Performance**: Lighthouse score > 90 all categories
- [ ] **Reliability**: 99.9% uptime
- [ ] **Security**: Zero critical vulnerabilities
- [ ] **Scalability**: Handle 1000+ concurrent users

---

## 📊 Analytics & Monitoring

### User Behavior Analytics
- **Feature Adoption**
  - % of users using AI assistant vs traditional UI
  - Most common AI commands
  - Command success vs failure rate

- **User Engagement**
  - Daily/Monthly active users
  - Average session duration
  - Feature usage heatmap

- **Performance Metrics**
  - Page load times
  - API response times
  - Error rates

### AI Metrics
- **Intent Parser Performance**
  - Intent classification accuracy
  - Entity extraction accuracy
  - Ambiguous request rate

- **Agent Performance**
  - Tool execution success rate
  - Average tools per workflow
  - User satisfaction per agent

- **Conversation Metrics**
  - Average conversation length
  - Multi-turn conversation rate
  - Abandonment rate

### Tools
- **PostHog** - Product analytics
- **Sentry** - Error tracking
- **Vercel Analytics** - Web vitals
- **Custom Dashboard** - AI-specific metrics

---

## 🔐 Security & Compliance

### Security Measures
- [ ] **Authentication**
  - JWT-based authentication
  - Session management
  - Role-based access control (RBAC)
  - Multi-factor authentication (MFA)

- [ ] **Data Protection**
  - HTTPS/TLS encryption in transit
  - Encrypted sensitive data at rest
  - HIPAA compliance for PHI
  - Audit logging

- [ ] **Input Validation**
  - Sanitize all user inputs
  - Validate AI-generated actions
  - Rate limiting
  - CSRF protection

### Compliance
- [ ] **HIPAA**
  - PHI encryption
  - Access controls
  - Audit trails
  - Business Associate Agreements

- [ ] **GDPR** (if applicable)
  - Data retention policies
  - Right to deletion
  - Data portability
  - Consent management

---

## 🌍 Internationalization (Future)

### Multi-language Support
- [ ] English (default)
- [ ] Hindi
- [ ] Regional languages
- [ ] RTL support (Arabic, Hebrew)

### Localization
- [ ] Date/time formatting
- [ ] Number formatting
- [ ] Currency
- [ ] Time zones

---

## 🔮 Future Enhancements (Post-MVP)

### Advanced AI Features
- [ ] **Predictive Analytics**
  - Predict no-show probability
  - Predict patient readmission risk
  - Optimize appointment scheduling
  - Journey completion forecasting

- [ ] **Automated Workflows**
  - Auto-assign tickets based on type
  - Auto-schedule follow-ups
  - Intelligent reminder timing
  - Smart journey adjustments

- [ ] **Voice Agent Improvements**
  - Multi-language support
  - Emotion detection
  - Accent handling
  - Background noise filtering

### Mobile Apps
- [ ] **iOS App** (React Native)
  - Native push notifications
  - Offline mode
  - Biometric authentication

- [ ] **Android App** (React Native)
  - Native push notifications
  - Offline mode
  - Biometric authentication

### Patient Portal
- [ ] Self-service appointment booking
- [ ] View test results
- [ ] Secure messaging with doctors
- [ ] View journey progress
- [ ] Payment portal

### Integrations
- [ ] **EHR Systems** (Epic, Cerner, FHIR)
- [ ] **Lab Systems** (LabCorp, Quest)
- [ ] **Pharmacy Systems**
- [ ] **Payment Gateways** (Stripe, Razorpay)
- [ ] **Telemedicine** (Zoom, Doxy.me)

---

## 📚 Documentation Plan

### Developer Documentation
- [ ] **Setup Guide** - Local development
- [ ] **Architecture Guide** - System design
- [ ] **Component Library** - Storybook
- [ ] **API Documentation** - Auto-generated
- [ ] **Agent Development Guide** - How to create new agents
- [ ] **Tool Development Guide** - How to create new tools

### User Documentation
- [ ] **User Manual** - Feature guide
- [ ] **Video Tutorials** - Recorded demos
- [ ] **AI Command Reference** - All supported commands
- [ ] **FAQ** - Common questions
- [ ] **Troubleshooting** - Common issues

---

## 🎓 Training Plan

### Staff Training
- [ ] **Onboarding Session** (2 hours)
  - Introduction to agent-native UX
  - Basic AI commands
  - Traditional UI navigation

- [ ] **Advanced Training** (4 hours)
  - Complex multi-step commands
  - Bulk operations
  - Reporting and analytics
  - Customization and preferences

- [ ] **Administrator Training** (8 hours)
  - Journey builder
  - Template management
  - User management
  - System configuration

### Training Materials
- [ ] Video tutorials
- [ ] Interactive demos
- [ ] Cheat sheets
- [ ] Practice environment

---

## 💡 Innovation Highlights

### What Makes This Revolutionary

1. **AI-First, Not AI-Added**
   - Unlike traditional CRMs with "AI features," this system is built AI-first
   - AI is the primary interface, not a sidebar feature

2. **Natural Language Everything**
   - Every operation can be done via natural language
   - No need to remember where buttons are
   - Talk to your system like a human assistant

3. **Specialized Agent Architecture**
   - Each domain has a dedicated expert agent
   - Agents can collaborate on complex tasks
   - Extensible: add new agents easily

4. **Hybrid UI/AI Model**
   - AI for speed and convenience
   - Traditional UI for visual browsing
   - Best of both worlds

5. **Voice-Native Healthcare**
   - Healthcare professionals work in fast-paced environments
   - Voice commands enable hands-free operation
   - Ideal for clinic/hospital workflows

6. **Confirmation-Before-Action**
   - AI suggests, human approves
   - Beautiful confirmation UI
   - Prevents accidental actions

7. **Context-Aware Proactivity**
   - AI suggests next actions based on context
   - Learns from user patterns
   - Reduces cognitive load

---

## 🏁 Conclusion

This agent-native PRM dashboard represents a **paradigm shift** in healthcare software UX. By making the AI assistant the primary interface and supporting it with specialized agents and tools, we enable healthcare staff to work at the speed of thought.

**Key Differentiators:**
- ✅ Natural language as primary interface
- ✅ Voice-enabled for hands-free operation
- ✅ Specialized agents for each domain
- ✅ Comprehensive tool system
- ✅ Beautiful confirmation UI
- ✅ Context-aware suggestions
- ✅ Hybrid AI/traditional UI
- ✅ World-class UX patterns from best CRMs

**Next Steps:**
1. Review and approve this architecture
2. Set up development environment
3. Begin Phase 1: Foundation
4. Iterate based on user feedback

---

**Prepared by:** Claude (Healthcare Systems & AI Expert)
**Date:** November 19, 2024
**Version:** 1.0
**Status:** Ready for Review & Implementation

---

## Appendix A: Example AI Conversations

### Example 1: Scheduling Appointment

```
User: "Schedule callback for patient arunank tomorrow at 2pm"

AI: 🔍 Searching for patient "arunank"...

AI: I found Arun Kumar (MRN: MR001234, Phone: 9844111173).
    Would you like to schedule a callback for tomorrow (Nov 20) at 2:00 PM?

    ┌─────────────────────────────────┐
    │ Callback Scheduling             │
    ├─────────────────────────────────┤
    │ Patient: Arun Kumar             │
    │ Phone: 9844111173               │
    │ Date: Nov 20, 2024              │
    │ Time: 2:00 PM                   │
    │ Type: Callback                  │
    │                                 │
    │ [Confirm & Schedule] [Modify]   │
    └─────────────────────────────────┘

User: "Confirm"

AI: ✅ Callback scheduled successfully!
    - Reminder will be sent to 9844111173
    - Added to your calendar
    - Notification set for 1:30 PM (30 min before)

    [View in Calendar] [Send Reminder Now]
```

---

### Example 2: Complex Multi-Step Workflow

```
User: "Schedule an appointment of arunank with dr. rajiv sharma from
       orthopaedics for tomorrow 10am"

AI: 🔍 Processing request...
    - Searching for patient "arunank"
    - Searching for practitioner "dr. rajiv sharma" in orthopaedics
    - Checking availability for tomorrow at 10:00 AM

AI: ✅ I found all the details:

    ┌──────────────────────────────────────────┐
    │ Appointment Booking                      │
    ├──────────────────────────────────────────┤
    │ Patient: Arun Kumar (9844111173)         │
    │ Practitioner: Dr. Rajiv Sharma           │
    │ Speciality: Orthopaedics                 │
    │ Date & Time: Nov 20, 2024 at 10:00 AM    │
    │ Duration: 30 minutes                     │
    │ Location: Main Clinic, Room 203          │
    │ Status: Available ✓                      │
    │                                          │
    │ Actions after booking:                   │
    │ ☑ Send WhatsApp confirmation            │
    │ ☑ Send calendar invite                  │
    │ ☑ Create pre-visit checklist            │
    │                                          │
    │ [Confirm & Book] [Modify] [Cancel]       │
    └──────────────────────────────────────────┘

User: "Confirm"

AI: ✅ Appointment booked successfully!

    - Appointment ID: APT-2024-001234
    - WhatsApp confirmation sent ✓✓
    - Calendar invite sent 📅
    - Pre-visit checklist created ✓

    Next suggested action:
    "Would you like to start a pre-visit journey for this patient?"

    [Start Journey] [View Appointment] [View Patient]
```

---

### Example 3: Bulk Operation

```
User: "Send reminder to all patients with appointments today"

AI: 🔍 Finding patients with appointments today...

AI: Found 12 patients with appointments today:

    ┌──────────────────────────────────────────┐
    │ Bulk Reminder Sending                    │
    ├──────────────────────────────────────────┤
    │ Recipients: 12 patients                  │
    │                                          │
    │ • 09:00 - Arun Kumar (9844111173)        │
    │ • 10:00 - Priya Sharma (9876543210)      │
    │ • 11:00 - John Doe (9123456789)          │
    │ • ... and 9 more                         │
    │                                          │
    │ Message Type: Appointment Reminder       │
    │ Channel: WhatsApp ✓                      │
    │ Template: "Your appointment today at..."  │
    │                                          │
    │ Estimated delivery: Within 2 minutes     │
    │                                          │
    │ [Send to All] [Preview Message] [Cancel] │
    └──────────────────────────────────────────┘

User: "Send to all"

AI: 📤 Sending reminders...

    Progress: ▓▓▓▓▓▓▓▓▓▓▓▓ 12/12 (100%)

    ✅ All reminders sent successfully!
    - 12 WhatsApp messages delivered
    - Average delivery time: 1.2 seconds

    [View Delivery Report] [Send Follow-up]
```

---

### Example 4: Information Retrieval

```
User: "Show me patients who missed appointments this week"

AI: 🔍 Searching for missed appointments this week...

AI: Found 5 patients who missed appointments:

    ┌──────────────────────────────────────────┐
    │ Missed Appointments (Nov 17-19)          │
    ├──────────────────────────────────────────┤
    │ 1. Sarah Miller (9111222333)             │
    │    - Nov 18, 10:00 AM with Dr. Priya     │
    │    - Status: No-show ⚠                  │
    │    - No prior cancellation               │
    │                                          │
    │ 2. Rajesh Kumar (9444555666)             │
    │    - Nov 17, 2:00 PM with Dr. Rajiv      │
    │    - Status: No-show ⚠                  │
    │    - Called 30 min after appointment     │
    │                                          │
    │ ... and 3 more                           │
    │                                          │
    │ Suggested Actions:                       │
    │ • Send follow-up message to all          │
    │ • Create tickets for investigation       │
    │ • Reschedule appointments                │
    │                                          │
    │ [View Full List] [Send Follow-up]        │
    └──────────────────────────────────────────┘

User: "Send follow-up to all"

AI: 📤 Sending follow-up messages...
    [Proceeds to send]
```

---

### Example 5: Voice Command

```
[User presses microphone button]

User: (Voice) "Hey PRM, complete the billing for patient nine eight four
                four one one one one seven three"

AI: 🎤 Transcript: "complete the billing for patient 9844111173"

    🔍 Processing...

AI: Found patient Arun Kumar (9844111173).

    ┌──────────────────────────────────────────┐
    │ Complete Billing                         │
    ├──────────────────────────────────────────┤
    │ Patient: Arun Kumar                      │
    │ Phone: 9844111173                        │
    │                                          │
    │ Recent Visit: Nov 18, 2024               │
    │ Services: Consultation - Orthopaedics    │
    │                                          │
    │ Amount: ₹1,500                           │
    │ Payment Method: [Select]                 │
    │                                          │
    │ [Cash] [Card] [UPI] [Insurance]          │
    └──────────────────────────────────────────┘

User: (Voice) "Cash"

AI: ✅ Billing completed!
    - Amount: ₹1,500
    - Payment: Cash
    - Receipt sent via WhatsApp

    [Print Receipt] [View Details]
```

---

