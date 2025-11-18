# AI System Documentation

## Overview

This is an **Agent-Native AI System** for the PRM Dashboard. Unlike traditional UIs where AI is "added on," this system makes AI the **primary interface** for interacting with the application.

## Architecture

```
User Input
    ↓
Orchestrator (main coordinator)
    ↓
Intent Parser (GPT-4) → Classifies intent, routes to agent
    ↓
Agent Registry → Finds appropriate agent
    ↓
Specialized Agent (AppointmentAgent, PatientAgent, etc.)
    ↓
Tool Execution (appointment.book, patient.search, etc.)
    ↓
Response Formatting (GPT-4)
    ↓
User-Friendly Response
```

## Core Components

### 1. Tools (`lib/ai/tools/`)

**What are Tools?**
- Atomic operations that agents can execute
- Examples: `appointment.book`, `patient.search`, `appointment.cancel`

**Tool Structure:**
```typescript
{
  name: 'appointment.book',
  description: 'Book a new appointment for a patient',
  parameters: {
    patient_id: { type: 'string', required: true },
    practitioner_id: { type: 'string', required: true },
    slot_id: { type: 'string', required: true },
  },
  execute: async (params, context) => { /* ... */ },
  requiresConfirmation: true,
  riskLevel: 'medium',
}
```

**Available Tools:**
- `appointment.check_availability` - Find available slots
- `appointment.book` - Book new appointment
- `appointment.cancel` - Cancel appointment
- `appointment.reschedule` - Reschedule appointment
- `appointment.get` - Get appointment details
- `patient.search` - Search for patients
- `patient.get` - Get patient by ID
- `patient.get_360_view` - Get complete patient view
- `patient.create` - Create new patient
- `patient.update` - Update patient info

### 2. Agents (`lib/ai/agents/`)

**What are Agents?**
- Specialized AI assistants that handle specific domains
- Use tools to accomplish tasks
- Convert natural language → structured actions

**Agent Workflow:**
1. **Analyze Intent** - Use GPT-4 to understand user request
2. **Plan Execution** - Create step-by-step plan with tools
3. **Execute Plan** - Run tools in sequence
4. **Format Response** - Convert results to natural language

**Available Agents:**

#### AppointmentAgent
Handles all appointment operations
```typescript
// Examples:
"Show me available slots for Dr. Smith next week"
"Book John Doe with cardiology tomorrow at 2pm"
"Cancel appointment APT123"
"Reschedule my 3pm to 5pm"
```

#### PatientAgent
Manages patient data and records
```typescript
// Examples:
"Search for patient John Doe"
"Find patient with phone 9844111173"
"Show me complete view for patient 123"
"Update patient email to newemail@example.com"
```

### 3. Intent Parser (`lib/ai/intent-parser.ts`)

**What does it do?**
- Uses GPT-4 to classify user intents
- Routes requests to the right agent
- Extracts entities (names, dates, IDs, etc.)

**Example:**
```typescript
Input: "Schedule a callback for patient John tomorrow at 2pm"

Output:
{
  agentName: "AppointmentAgent",
  confidence: 0.95,
  intent: "Schedule appointment callback",
  entities: {
    patientName: "John",
    date: "tomorrow",
    time: "2pm",
    type: "callback"
  }
}
```

### 4. Orchestrator (`lib/ai/orchestrator.ts`)

**What does it do?**
- Main entry point for all AI interactions
- Coordinates intent parsing, agent selection, execution
- Manages conversation history
- Handles multi-agent workflows

**Features:**
- Single-agent execution
- Multi-agent chains (e.g., search patient → book appointment)
- Conversation context tracking
- Error handling and recovery

## Usage

### Basic Setup

```typescript
import { initializeAISystem, processUserInput } from '@/lib/ai';

// Initialize the system
initializeAISystem(process.env.OPENAI_API_KEY);

// Process user input
const result = await processUserInput(
  "Book John Doe with Dr. Smith tomorrow at 2pm",
  'user_123',      // userId
  'org_456',       // orgId
  'session_789',   // sessionId
  ['appointments.write', 'patients.read'] // permissions
);

console.log(result.message); // "I've booked an appointment for John Doe..."
```

### In a React Component

```typescript
'use client';
import { useState } from 'react';
import { processUserInput } from '@/lib/ai';

export function AIAssistant() {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState('');

  const handleSubmit = async () => {
    const result = await processUserInput(
      input,
      'user_123',
      'org_456',
      'session_789'
    );

    setResponse(result.message);
  };

  return (
    <div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="What would you like to do?"
      />
      <button onClick={handleSubmit}>Send</button>
      <div>{response}</div>
    </div>
  );
}
```

## Execution Context

Every tool and agent receives an `ExecutionContext`:

```typescript
interface ExecutionContext {
  userId: string;         // Who is making the request
  orgId: string;          // Which organization
  sessionId: string;      // Conversation session
  requestId: string;      // Unique request ID
  permissions: string[];  // User permissions
}
```

This enables:
- Permission checking
- Audit logging
- User-specific behavior
- Multi-tenancy

## Result Structure

All operations return a standardized result:

```typescript
interface OrchestratorResult {
  success: boolean;
  message: string;              // User-friendly message
  agentsUsed: string[];         // Which agents were involved
  results: AgentResult[];       // Detailed results from each agent
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    executionTime?: number;
    totalSteps?: number;
    classification?: IntentClassification;
  };
}
```

## Confirmation Workflow

For high-risk operations (create, update, delete), the system requires confirmation:

```typescript
// User: "Cancel appointment APT123"

// Step 1: System creates plan and requests confirmation
const result = await processUserInput("Cancel appointment APT123", ...);

if (result.results[0].data?.requiresConfirmation) {
  const plan = result.results[0].data.plan;

  // Step 2: Show plan to user for approval
  // UI displays: "I'm about to cancel appointment APT123. Confirm?"

  // Step 3: User confirms
  const agent = agentRegistry.getAgent('AppointmentAgent');
  const confirmed = await agent.executeWithConfirmation(plan, context);
}
```

## Example Commands

### Appointments
```
"Show me available slots for Dr. Smith next week"
"Book John Doe with cardiology tomorrow at 2pm"
"Cancel appointment APT123"
"Reschedule my 3pm appointment to 5pm"
"What appointments do I have today?"
```

### Patients
```
"Search for patient John Doe"
"Find patient with phone 9844111173"
"Show me complete view for patient 123"
"Create patient Mary Smith with phone 9876543210"
"Update patient email to newemail@example.com"
```

### Complex Multi-Agent
```
"Book John Doe for a cardiology consultation next week"
→ PatientAgent searches for John Doe
→ AppointmentAgent checks availability
→ AppointmentAgent books the slot

"Send appointment reminder to all patients scheduled for tomorrow"
→ AppointmentAgent gets tomorrow's appointments
→ CommunicationAgent sends reminders
```

## Adding New Tools

```typescript
// 1. Create tool in lib/ai/tools/your-tool.ts
export const yourTool: Tool = {
  name: 'your_category.action',
  description: 'What this tool does',
  parameters: {
    param1: { type: 'string', required: true },
  },
  execute: async (params, context) => {
    // Your logic here
    return { success: true, data: result };
  },
  requiresConfirmation: false,
  riskLevel: 'low',
};

// 2. Register in lib/ai/index.ts
import { yourTool } from './tools/your-tool';
toolRegistry.registerTools([yourTool], 'your_category');
```

## Adding New Agents

```typescript
// 1. Create agent extending BaseAgent
import { BaseAgent, AgentPlan } from './BaseAgent';

export class YourAgent extends BaseAgent {
  constructor(openaiApiKey?: string) {
    super(
      'YourAgent',
      'description of what this agent does',
      ['tool.name1', 'tool.name2'], // Available tools
      openaiApiKey
    );
  }

  protected async planExecution(intent, context): Promise<AgentPlan> {
    // Use GPT-4 to create execution plan
    // Return { steps, reasoning, requiresConfirmation }
  }

  protected async formatResponse(results, intent): Promise<string> {
    // Use GPT-4 to format results into natural language
  }

  canHandle(intent: string): boolean {
    // Return true if this agent can handle the intent
  }
}

// 2. Register in lib/ai/index.ts
const yourAgent = new YourAgent(openaiApiKey);
agentRegistry.registerAgent(yourAgent, yourAgent.getCapabilities(), 10);
```

## Testing

```typescript
import { initializeAISystem, processUserInput } from '@/lib/ai';

// Initialize
initializeAISystem(process.env.OPENAI_API_KEY);

// Test
const result = await processUserInput(
  "Show available slots for cardiology tomorrow",
  'test_user',
  'test_org',
  'test_session'
);

expect(result.success).toBe(true);
expect(result.agentsUsed).toContain('AppointmentAgent');
```

## Error Handling

The system provides multiple levels of error handling:

1. **Tool Level** - Tools return `{ success: false, error: {...} }`
2. **Agent Level** - Agents catch tool errors and provide suggestions
3. **Orchestrator Level** - Catches all errors, provides fallback messages
4. **Intent Parser Level** - Requests clarification when confidence is low

## Performance

- **Intent Classification**: ~500-1000ms (GPT-4 API call)
- **Agent Planning**: ~500-1000ms (GPT-4 API call)
- **Tool Execution**: 100-500ms (API calls to backend)
- **Response Formatting**: ~300-500ms (GPT-4 API call)

**Total**: 1.5-3 seconds for typical requests

**Optimizations:**
- Cache common intents
- Parallel tool execution where possible
- Use faster models for simple tasks
- Stream responses to user

## Security Considerations

1. **Permission Checking** - All tools check `context.permissions`
2. **Confirmation Required** - High-risk actions need user approval
3. **Audit Logging** - All actions logged with `context.requestId`
4. **Input Validation** - All tool parameters validated before execution
5. **Rate Limiting** - Implement per-user/session rate limits
6. **API Key Security** - Never expose OpenAI API key to client

## Future Enhancements

- [ ] Journey management agent
- [ ] Communication agent (WhatsApp, SMS, Email)
- [ ] Billing agent
- [ ] Ticket management agent
- [ ] Analytics agent
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Learning from user feedback
- [ ] Proactive suggestions

## Troubleshooting

**"Agent not found"**
- Make sure you called `initializeAISystem()` before using the system

**"Tool execution failed"**
- Check API connectivity
- Verify user permissions
- Check tool parameter validation

**"Low confidence classification"**
- User input may be ambiguous
- System will request clarification automatically

**"OpenAI API errors"**
- Verify API key is set
- Check rate limits
- Ensure API key has sufficient credits

## License

This AI system is part of the PRM Dashboard project.
