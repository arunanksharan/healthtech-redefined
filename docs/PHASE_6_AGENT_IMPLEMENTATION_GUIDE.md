# Phase 6: Agent & Tool Implementation Guide

**Date:** November 19, 2024
**Purpose:** Detailed guide for implementing AI agents and tools
**Audience:** Frontend developers, AI engineers

---

## 📚 Table of Contents

1. [Agent Architecture Overview](#agent-architecture-overview)
2. [Tool System Implementation](#tool-system-implementation)
3. [Creating a New Agent](#creating-a-new-agent)
4. [Creating a New Tool](#creating-a-new-tool)
5. [Intent Parsing](#intent-parsing)
6. [Agent Orchestration](#agent-orchestration)
7. [Error Handling](#error-handling)
8. [Testing Agents](#testing-agents)
9. [Best Practices](#best-practices)

---

## 🏗️ Agent Architecture Overview

### Core Concepts

**Agent**: An AI-powered component that handles specific domain operations (appointments, journeys, billing, etc.)

**Tool**: An atomic backend operation that an agent can use (API calls, database queries, calculations)

**Intent**: The user's goal extracted from natural language (e.g., "book_appointment", "send_message")

**Orchestrator**: The central system that routes intents to appropriate agents

---

## 🛠️ Tool System Implementation

### 1. Tool Interface Definition

```typescript
// lib/ai/tools/types.ts

export interface Tool {
  name: string;
  description: string;
  parameters: ToolParameters;
  execute: (params: any, context: ExecutionContext) => Promise<ToolResult>;
  requiresConfirmation?: boolean;
  riskLevel?: 'low' | 'medium' | 'high';
}

export interface ToolParameters {
  [key: string]: {
    type: 'string' | 'number' | 'boolean' | 'object' | 'array';
    description: string;
    required: boolean;
    enum?: string[];
    default?: any;
  };
}

export interface ToolResult {
  success: boolean;
  data?: any;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    executionTime: number;
    cacheHit?: boolean;
  };
}

export interface ExecutionContext {
  userId: string;
  orgId: string;
  sessionId: string;
  requestId: string;
  permissions: string[];
}
```

---

### 2. Tool Registry

```typescript
// lib/ai/tools/registry.ts

import { Tool } from './types';
import { appointmentTools } from './appointment-tools';
import { patientTools } from './patient-tools';
import { journeyTools } from './journey-tools';
import { communicationTools } from './communication-tools';
import { billingTools } from './billing-tools';

class ToolRegistry {
  private tools: Map<string, Tool> = new Map();

  constructor() {
    this.registerTools([
      ...appointmentTools,
      ...patientTools,
      ...journeyTools,
      ...communicationTools,
      ...billingTools
    ]);
  }

  registerTools(tools: Tool[]) {
    tools.forEach(tool => {
      this.tools.set(tool.name, tool);
    });
  }

  getTool(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  getAllTools(): Tool[] {
    return Array.from(this.tools.values());
  }

  getToolsByCategory(category: string): Tool[] {
    return this.getAllTools().filter(tool =>
      tool.name.startsWith(category)
    );
  }

  async executeTool(
    toolName: string,
    params: any,
    context: ExecutionContext
  ): Promise<ToolResult> {
    const tool = this.getTool(toolName);
    if (!tool) {
      return {
        success: false,
        error: {
          code: 'TOOL_NOT_FOUND',
          message: `Tool ${toolName} not found`
        }
      };
    }

    try {
      const startTime = Date.now();
      const result = await tool.execute(params, context);
      const executionTime = Date.now() - startTime;

      return {
        ...result,
        metadata: {
          ...result.metadata,
          executionTime
        }
      };
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'TOOL_EXECUTION_ERROR',
          message: error.message,
          details: error
        }
      };
    }
  }
}

export const toolRegistry = new ToolRegistry();
```

---

### 3. Example Tool Implementation: Appointment Tools

```typescript
// lib/ai/tools/appointment-tools.ts

import { Tool } from './types';
import { api } from '@/lib/api/client';

export const appointmentTools: Tool[] = [
  {
    name: 'appointment.check_availability',
    description: 'Check available appointment slots for a practitioner',
    parameters: {
      practitioner_id: {
        type: 'string',
        description: 'ID of the practitioner',
        required: false
      },
      speciality: {
        type: 'string',
        description: 'Medical speciality (e.g., cardiology, orthopaedics)',
        required: false
      },
      date_start: {
        type: 'string',
        description: 'Start date for availability check (ISO 8601)',
        required: true
      },
      date_end: {
        type: 'string',
        description: 'End date for availability check (ISO 8601)',
        required: true
      },
      location_id: {
        type: 'string',
        description: 'Clinic/hospital location ID',
        required: false
      },
      duration: {
        type: 'number',
        description: 'Appointment duration in minutes',
        required: false,
        default: 30
      }
    },
    execute: async (params, context) => {
      try {
        const response = await api.get('/api/v1/prm/appointments/slots', {
          params: {
            ...params,
            org_id: context.orgId
          }
        });

        return {
          success: true,
          data: response.data
        };
      } catch (error) {
        return {
          success: false,
          error: {
            code: 'AVAILABILITY_CHECK_FAILED',
            message: 'Failed to check appointment availability',
            details: error
          }
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low'
  },

  {
    name: 'appointment.book',
    description: 'Book an appointment slot',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true
      },
      practitioner_id: {
        type: 'string',
        description: 'ID of the practitioner',
        required: true
      },
      slot_id: {
        type: 'string',
        description: 'ID of the available slot',
        required: true
      },
      appointment_type: {
        type: 'string',
        description: 'Type of appointment',
        required: true,
        enum: ['consultation', 'follow_up', 'procedure', 'test']
      },
      notes: {
        type: 'string',
        description: 'Additional notes for the appointment',
        required: false
      },
      send_confirmation: {
        type: 'boolean',
        description: 'Whether to send confirmation message',
        required: false,
        default: true
      }
    },
    execute: async (params, context) => {
      try {
        // 1. Book the appointment
        const response = await api.post('/api/v1/prm/appointments', {
          ...params,
          org_id: context.orgId,
          booked_by: context.userId
        });

        const appointment = response.data;

        // 2. Send confirmation if requested
        if (params.send_confirmation) {
          await api.post('/api/v1/prm/communications', {
            patient_id: params.patient_id,
            channel: 'whatsapp',
            template_id: 'appointment_confirmation',
            context: {
              appointment_id: appointment.id,
              practitioner_name: appointment.practitioner.name,
              date_time: appointment.start_time,
              location: appointment.location.name
            },
            org_id: context.orgId
          });
        }

        return {
          success: true,
          data: {
            appointment,
            confirmation_sent: params.send_confirmation
          }
        };
      } catch (error) {
        return {
          success: false,
          error: {
            code: 'BOOKING_FAILED',
            message: 'Failed to book appointment',
            details: error
          }
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium'
  },

  {
    name: 'appointment.cancel',
    description: 'Cancel an existing appointment',
    parameters: {
      appointment_id: {
        type: 'string',
        description: 'ID of the appointment to cancel',
        required: true
      },
      reason: {
        type: 'string',
        description: 'Reason for cancellation',
        required: false
      },
      notify_patient: {
        type: 'boolean',
        description: 'Whether to notify the patient',
        required: false,
        default: true
      }
    },
    execute: async (params, context) => {
      try {
        const response = await api.patch(
          `/api/v1/prm/appointments/${params.appointment_id}`,
          {
            status: 'cancelled',
            cancellation_reason: params.reason,
            cancelled_by: context.userId,
            org_id: context.orgId
          }
        );

        if (params.notify_patient) {
          await api.post('/api/v1/prm/communications', {
            patient_id: response.data.patient_id,
            channel: 'whatsapp',
            template_id: 'appointment_cancellation',
            context: {
              appointment_id: params.appointment_id,
              reason: params.reason
            },
            org_id: context.orgId
          });
        }

        return {
          success: true,
          data: response.data
        };
      } catch (error) {
        return {
          success: false,
          error: {
            code: 'CANCELLATION_FAILED',
            message: 'Failed to cancel appointment',
            details: error
          }
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium'
  },

  {
    name: 'appointment.reschedule',
    description: 'Reschedule an existing appointment',
    parameters: {
      appointment_id: {
        type: 'string',
        description: 'ID of the appointment to reschedule',
        required: true
      },
      new_slot_id: {
        type: 'string',
        description: 'ID of the new slot',
        required: true
      },
      reason: {
        type: 'string',
        description: 'Reason for rescheduling',
        required: false
      },
      notify_patient: {
        type: 'boolean',
        description: 'Whether to notify the patient',
        required: false,
        default: true
      }
    },
    execute: async (params, context) => {
      try {
        const response = await api.patch(
          `/api/v1/prm/appointments/${params.appointment_id}/reschedule`,
          {
            new_slot_id: params.new_slot_id,
            reason: params.reason,
            rescheduled_by: context.userId,
            org_id: context.orgId
          }
        );

        if (params.notify_patient) {
          await api.post('/api/v1/prm/communications', {
            patient_id: response.data.patient_id,
            channel: 'whatsapp',
            template_id: 'appointment_rescheduled',
            context: {
              appointment_id: params.appointment_id,
              new_date_time: response.data.start_time
            },
            org_id: context.orgId
          });
        }

        return {
          success: true,
          data: response.data
        };
      } catch (error) {
        return {
          success: false,
          error: {
            code: 'RESCHEDULE_FAILED',
            message: 'Failed to reschedule appointment',
            details: error
          }
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium'
  }
];
```

---

## 🤖 Creating a New Agent

### 1. Base Agent Class

```typescript
// lib/ai/agents/BaseAgent.ts

import { Tool, ToolResult, ExecutionContext } from '../tools/types';
import { toolRegistry } from '../tools/registry';
import OpenAI from 'openai';

export interface AgentConfig {
  name: string;
  description: string;
  systemPrompt: string;
  tools: string[]; // Tool names this agent can use
  llm?: 'gpt-4-turbo' | 'gpt-4' | 'gpt-3.5-turbo';
  temperature?: number;
  maxTokens?: number;
}

export interface AgentResult {
  success: boolean;
  data?: any;
  message: string;
  toolsUsed: string[];
  confirmationRequired?: boolean;
  confirmationData?: any;
  error?: {
    code: string;
    message: string;
  };
}

export abstract class BaseAgent {
  protected openai: OpenAI;
  protected config: AgentConfig;
  protected tools: Tool[];

  constructor(config: AgentConfig) {
    this.config = {
      llm: 'gpt-4-turbo',
      temperature: 0.1,
      maxTokens: 2000,
      ...config
    };

    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });

    // Load tools from registry
    this.tools = config.tools
      .map(name => toolRegistry.getTool(name))
      .filter((tool): tool is Tool => tool !== undefined);
  }

  /**
   * Main execution method - override in subclasses for custom logic
   */
  async execute(
    userIntent: string,
    context: ExecutionContext
  ): Promise<AgentResult> {
    try {
      // 1. Analyze the user's intent
      const understanding = await this.analyzeIntent(userIntent, context);

      // 2. Plan the execution
      const plan = await this.planExecution(understanding, context);

      // 3. Execute the plan
      const result = await this.executePlan(plan, context);

      // 4. Format the response
      return this.formatResponse(result);
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute agent',
        toolsUsed: [],
        error: {
          code: 'AGENT_EXECUTION_ERROR',
          message: error.message
        }
      };
    }
  }

  /**
   * Analyze user intent using LLM
   */
  protected async analyzeIntent(
    userIntent: string,
    context: ExecutionContext
  ): Promise<any> {
    const response = await this.openai.chat.completions.create({
      model: this.config.llm!,
      temperature: this.config.temperature,
      max_tokens: 500,
      messages: [
        {
          role: 'system',
          content: this.config.systemPrompt
        },
        {
          role: 'user',
          content: `Analyze this request and extract structured information:\n\n"${userIntent}"\n\nExtract: intent, entities, confidence, clarifications_needed`
        }
      ],
      response_format: { type: 'json_object' }
    });

    return JSON.parse(response.choices[0].message.content || '{}');
  }

  /**
   * Plan execution steps - override in subclasses
   */
  protected abstract planExecution(
    understanding: any,
    context: ExecutionContext
  ): Promise<any>;

  /**
   * Execute the planned steps
   */
  protected async executePlan(plan: any, context: ExecutionContext): Promise<any> {
    const results = [];
    const toolsUsed = [];

    for (const step of plan.steps) {
      const toolResult = await toolRegistry.executeTool(
        step.tool,
        step.params,
        context
      );

      toolsUsed.push(step.tool);
      results.push(toolResult);

      if (!toolResult.success) {
        // Stop execution on first error
        break;
      }
    }

    return {
      results,
      toolsUsed
    };
  }

  /**
   * Format the final response - override in subclasses
   */
  protected abstract formatResponse(executionResult: any): AgentResult;

  /**
   * Helper: Get available tools info for LLM
   */
  protected getToolsInfo(): string {
    return this.tools
      .map(
        tool => `
Tool: ${tool.name}
Description: ${tool.description}
Parameters: ${JSON.stringify(tool.parameters, null, 2)}
---`
      )
      .join('\n');
  }
}
```

---

### 2. Example Agent Implementation: Appointment Agent

```typescript
// lib/ai/agents/AppointmentAgent.ts

import { BaseAgent, AgentConfig, AgentResult } from './BaseAgent';
import { ExecutionContext } from '../tools/types';

export class AppointmentAgent extends BaseAgent {
  constructor() {
    const config: AgentConfig = {
      name: 'AppointmentAgent',
      description: 'Handles appointment booking, rescheduling, and management',
      systemPrompt: `You are an expert appointment scheduling assistant for a healthcare system.
Your job is to help staff book, reschedule, cancel, and manage patient appointments.

Available tools:
- appointment.check_availability: Check available slots
- appointment.book: Book a new appointment
- appointment.cancel: Cancel an appointment
- appointment.reschedule: Reschedule an appointment
- patient.search: Search for patients
- practitioner.search: Search for practitioners

When booking appointments:
1. First, identify the patient (search if needed)
2. Identify the practitioner (search if needed)
3. Check availability
4. Book the slot
5. Send confirmation

Always be proactive about sending confirmations and creating follow-up tasks.
If information is missing or ambiguous, ask for clarification.`,
      tools: [
        'appointment.check_availability',
        'appointment.book',
        'appointment.cancel',
        'appointment.reschedule',
        'patient.search',
        'practitioner.search'
      ],
      llm: 'gpt-4-turbo',
      temperature: 0.1
    };

    super(config);
  }

  protected async planExecution(understanding: any, context: ExecutionContext): Promise<any> {
    const { intent, entities } = understanding;

    // Use LLM to create execution plan
    const response = await this.openai.chat.completions.create({
      model: this.config.llm!,
      temperature: 0.1,
      messages: [
        {
          role: 'system',
          content: `You are creating an execution plan for appointment operations.
Available tools:
${this.getToolsInfo()}

Create a step-by-step plan to fulfill the user's request.
Return a JSON object with this structure:
{
  "steps": [
    {
      "tool": "tool_name",
      "params": { ... },
      "description": "what this step does"
    }
  ],
  "requiresConfirmation": boolean,
  "summary": "brief summary of what will happen"
}`
        },
        {
          role: 'user',
          content: `Intent: ${intent}\nEntities: ${JSON.stringify(entities)}\n\nCreate execution plan:`
        }
      ],
      response_format: { type: 'json_object' }
    });

    return JSON.parse(response.choices[0].message.content || '{}');
  }

  protected formatResponse(executionResult: any): AgentResult {
    const { results, toolsUsed } = executionResult;

    // Check if all tools succeeded
    const allSucceeded = results.every((r: any) => r.success);

    if (!allSucceeded) {
      const firstError = results.find((r: any) => !r.success);
      return {
        success: false,
        message: `Failed to complete operation: ${firstError.error.message}`,
        toolsUsed,
        error: firstError.error
      };
    }

    // Get the last result (usually the main action)
    const mainResult = results[results.length - 1];

    // Format success message based on what was done
    let message = '';
    let confirmationData = null;

    if (toolsUsed.includes('appointment.book')) {
      const appointment = mainResult.data.appointment;
      message = `Appointment booked successfully for ${appointment.patient.name} with ${appointment.practitioner.name} on ${new Date(appointment.start_time).toLocaleString()}`;
      confirmationData = {
        type: 'appointment_booked',
        appointment
      };
    } else if (toolsUsed.includes('appointment.cancel')) {
      message = 'Appointment cancelled successfully';
      confirmationData = {
        type: 'appointment_cancelled',
        appointment: mainResult.data
      };
    } else if (toolsUsed.includes('appointment.reschedule')) {
      message = 'Appointment rescheduled successfully';
      confirmationData = {
        type: 'appointment_rescheduled',
        appointment: mainResult.data
      };
    }

    return {
      success: true,
      message,
      data: mainResult.data,
      toolsUsed,
      confirmationRequired: true,
      confirmationData
    };
  }

  /**
   * Custom method: Find next available slot
   */
  async findNextAvailable(
    practitionerId: string,
    startDate: Date,
    context: ExecutionContext
  ): Promise<any> {
    // Implementation for finding next available slot
    // This is a helper method specific to AppointmentAgent
  }
}
```

---

### 3. More Example Agents

```typescript
// lib/ai/agents/JourneyAgent.ts

export class JourneyAgent extends BaseAgent {
  constructor() {
    super({
      name: 'JourneyAgent',
      description: 'Manages patient care journeys',
      systemPrompt: `You are an expert care journey orchestration assistant...`,
      tools: [
        'journey.create_instance',
        'journey.advance_stage',
        'journey.pause',
        'journey.resume',
        'journey.get_status',
        'patient.search'
      ]
    });
  }

  // ... implementation
}

// lib/ai/agents/CommunicationAgent.ts

export class CommunicationAgent extends BaseAgent {
  constructor() {
    super({
      name: 'CommunicationAgent',
      description: 'Handles patient communications',
      systemPrompt: `You are an expert patient communication assistant...`,
      tools: [
        'communication.send_whatsapp',
        'communication.send_sms',
        'communication.send_email',
        'communication.bulk_send',
        'communication.get_templates',
        'patient.search'
      ]
    });
  }

  // ... implementation
}

// lib/ai/agents/BillingAgent.ts

export class BillingAgent extends BaseAgent {
  constructor() {
    super({
      name: 'BillingAgent',
      description: 'Manages billing and payments',
      systemPrompt: `You are an expert billing assistant...`,
      tools: [
        'billing.complete',
        'billing.generate_invoice',
        'billing.process_payment',
        'billing.send_receipt',
        'patient.search'
      ]
    });
  }

  // ... implementation
}
```

---

## 🔀 Intent Parsing

```typescript
// lib/ai/intent-parser.ts

import OpenAI from 'openai';

export interface ParsedIntent {
  intent: string;
  entities: Record<string, any>;
  confidence: number;
  ambiguous: boolean;
  clarifications_needed?: string[];
}

const INTENT_CATEGORIES = [
  'book_appointment',
  'cancel_appointment',
  'reschedule_appointment',
  'send_message',
  'create_journey',
  'advance_journey',
  'search_patient',
  'update_patient',
  'complete_billing',
  'create_ticket',
  'get_status',
  'fetch_information'
];

export class IntentParser {
  private openai: OpenAI;

  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
  }

  async parse(userInput: string): Promise<ParsedIntent> {
    const response = await this.openai.chat.completions.create({
      model: 'gpt-4-turbo',
      temperature: 0.1,
      messages: [
        {
          role: 'system',
          content: `You are an intent parser for a healthcare PRM system.
Your job is to extract the user's intent and relevant entities from their natural language input.

Available intents: ${INTENT_CATEGORIES.join(', ')}

Extract:
1. intent: The main action the user wants to perform
2. entities: All relevant information (patient identifiers, dates, times, names, etc.)
3. confidence: How confident you are (0.0 to 1.0)
4. ambiguous: Whether the request is ambiguous
5. clarifications_needed: List of things that need clarification

Return a JSON object with this structure:
{
  "intent": "intent_name",
  "entities": {
    "entity_name": "value",
    ...
  },
  "confidence": 0.95,
  "ambiguous": false,
  "clarifications_needed": []
}`
        },
        {
          role: 'user',
          content: userInput
        }
      ],
      response_format: { type: 'json_object' }
    });

    const parsed = JSON.parse(response.choices[0].message.content || '{}');
    return parsed as ParsedIntent;
  }

  /**
   * Parse with context (previous conversation)
   */
  async parseWithContext(
    userInput: string,
    conversationHistory: Array<{ role: string; content: string }>
  ): Promise<ParsedIntent> {
    const response = await this.openai.chat.completions.create({
      model: 'gpt-4-turbo',
      temperature: 0.1,
      messages: [
        {
          role: 'system',
          content: `You are an intent parser with conversation context...`
        },
        ...conversationHistory.slice(-5), // Last 5 messages
        {
          role: 'user',
          content: userInput
        }
      ],
      response_format: { type: 'json_object' }
    });

    return JSON.parse(response.choices[0].message.content || '{}');
  }
}

export const intentParser = new IntentParser();
```

---

## 🎯 Agent Orchestrator

```typescript
// lib/ai/orchestrator.ts

import { BaseAgent, AgentResult } from './agents/BaseAgent';
import { AppointmentAgent } from './agents/AppointmentAgent';
import { JourneyAgent } from './agents/JourneyAgent';
import { CommunicationAgent } from './agents/CommunicationAgent';
import { BillingAgent } from './agents/BillingAgent';
import { PatientAgent } from './agents/PatientAgent';
import { TicketAgent } from './agents/TicketAgent';
import { intentParser, ParsedIntent } from './intent-parser';
import { ExecutionContext } from './tools/types';

class AgentOrchestrator {
  private agents: Map<string, BaseAgent>;

  constructor() {
    this.agents = new Map([
      ['appointment', new AppointmentAgent()],
      ['journey', new JourneyAgent()],
      ['communication', new CommunicationAgent()],
      ['billing', new BillingAgent()],
      ['patient', new PatientAgent()],
      ['ticket', new TicketAgent()]
    ]);
  }

  /**
   * Main entry point: Execute a natural language command
   */
  async execute(
    userCommand: string,
    context: ExecutionContext
  ): Promise<AgentResult> {
    try {
      // 1. Parse intent
      const intent = await intentParser.parse(userCommand);

      // 2. Handle ambiguous requests
      if (intent.ambiguous || intent.confidence < 0.7) {
        return {
          success: false,
          message: 'I need more information to complete this request.',
          toolsUsed: [],
          error: {
            code: 'AMBIGUOUS_REQUEST',
            message: intent.clarifications_needed?.join(', ') || 'Please provide more details'
          }
        };
      }

      // 3. Route to appropriate agent
      const agent = this.routeToAgent(intent);
      if (!agent) {
        return {
          success: false,
          message: `I don't know how to handle "${intent.intent}"`,
          toolsUsed: [],
          error: {
            code: 'NO_AGENT_FOUND',
            message: `No agent registered for intent: ${intent.intent}`
          }
        };
      }

      // 4. Execute with agent
      const result = await agent.execute(userCommand, context);

      return result;
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute command',
        toolsUsed: [],
        error: {
          code: 'ORCHESTRATION_ERROR',
          message: error.message
        }
      };
    }
  }

  /**
   * Route intent to appropriate agent
   */
  private routeToAgent(intent: ParsedIntent): BaseAgent | null {
    const intentToAgent: Record<string, string> = {
      book_appointment: 'appointment',
      cancel_appointment: 'appointment',
      reschedule_appointment: 'appointment',
      send_message: 'communication',
      send_whatsapp: 'communication',
      send_sms: 'communication',
      bulk_message: 'communication',
      create_journey: 'journey',
      advance_journey: 'journey',
      pause_journey: 'journey',
      search_patient: 'patient',
      create_patient: 'patient',
      update_patient: 'patient',
      complete_billing: 'billing',
      generate_invoice: 'billing',
      create_ticket: 'ticket',
      assign_ticket: 'ticket'
    };

    const agentName = intentToAgent[intent.intent];
    return agentName ? this.agents.get(agentName) || null : null;
  }

  /**
   * Get all registered agents
   */
  getAgents(): BaseAgent[] {
    return Array.from(this.agents.values());
  }
}

export const orchestrator = new AgentOrchestrator();
```

---

## 🧪 Testing Agents

```typescript
// lib/ai/agents/__tests__/AppointmentAgent.test.ts

import { AppointmentAgent } from '../AppointmentAgent';
import { ExecutionContext } from '../../tools/types';

describe('AppointmentAgent', () => {
  let agent: AppointmentAgent;
  let context: ExecutionContext;

  beforeEach(() => {
    agent = new AppointmentAgent();
    context = {
      userId: 'user-123',
      orgId: 'org-456',
      sessionId: 'session-789',
      requestId: 'req-001',
      permissions: ['appointments:read', 'appointments:write']
    };
  });

  it('should book an appointment successfully', async () => {
    const command = 'Schedule appointment for patient arunank with dr. rajiv tomorrow at 10am';

    const result = await agent.execute(command, context);

    expect(result.success).toBe(true);
    expect(result.toolsUsed).toContain('appointment.book');
    expect(result.confirmationRequired).toBe(true);
  });

  it('should handle missing patient gracefully', async () => {
    const command = 'Schedule appointment with dr. rajiv tomorrow at 10am';

    const result = await agent.execute(command, context);

    expect(result.success).toBe(false);
    expect(result.error?.code).toBe('MISSING_PATIENT');
  });

  it('should reschedule appointment', async () => {
    const command = 'Reschedule appointment APT-123 to next Monday at 2pm';

    const result = await agent.execute(command, context);

    expect(result.success).toBe(true);
    expect(result.toolsUsed).toContain('appointment.reschedule');
  });
});
```

---

## ✅ Best Practices

### 1. Agent Design
- Keep agents focused on a single domain
- Make agents composable (they can call each other if needed)
- Always validate input before executing tools
- Provide clear error messages
- Log all agent executions for debugging

### 2. Tool Design
- Tools should be atomic (do one thing)
- Tools should be idempotent where possible
- Always validate parameters
- Return structured errors
- Include execution metadata

### 3. Error Handling
- Never throw errors, return error results
- Provide actionable error messages
- Log errors with context
- Gracefully degrade when tools fail

### 4. Security
- Always validate permissions in execution context
- Never expose sensitive data in error messages
- Audit all high-risk operations
- Rate limit agent executions

### 5. Performance
- Cache LLM responses when possible
- Implement timeouts for tool execution
- Use streaming for long operations
- Optimize tool execution order

### 6. User Experience
- Always confirm high-risk actions
- Provide progress indicators
- Show which tools are being used
- Allow undo for reversible operations

---

## 📝 Adding a New Tool Checklist

- [ ] Define tool interface with clear parameters
- [ ] Implement execute function
- [ ] Add error handling
- [ ] Set requiresConfirmation flag
- [ ] Set riskLevel
- [ ] Write unit tests
- [ ] Add to tool registry
- [ ] Update agent that uses it
- [ ] Document in tool reference

---

## 📝 Adding a New Agent Checklist

- [ ] Extend BaseAgent class
- [ ] Define system prompt
- [ ] List required tools
- [ ] Implement planExecution method
- [ ] Implement formatResponse method
- [ ] Write unit tests
- [ ] Add to agent orchestrator
- [ ] Update intent parser
- [ ] Document agent capabilities

---

**Last Updated:** November 19, 2024
**Status:** Ready for Implementation
