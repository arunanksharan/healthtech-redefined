# AI Assistant Chat Widget - Implementation Guide

**Purpose:** Comprehensive UI/UX implementation guide using Vercel AI SDK + shadcn/ui
**Tech Stack:** Next.js 14+, Vercel AI SDK (`@ai-sdk/react`), shadcn/ui, TanStack Query, Zustand

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Backend API Alignment](#2-backend-api-alignment)
3. [Project Setup](#3-project-setup)
4. [Core Components](#4-core-components)
5. [AI Tools & Generative UI](#5-ai-tools--generative-ui)
6. [Voice Input Integration](#6-voice-input-integration)
7. [State Management](#7-state-management)
8. [Visual Specifications](#8-visual-specifications)
9. [File Structure](#9-file-structure)
10. [Complete Component Code](#10-complete-component-code)

---

## 1. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        AI ASSISTANT WIDGET                                 │  │
│  │                                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │  │
│  │  │  useChat Hook   │  │  Tool Results   │  │  Voice Input    │           │  │
│  │  │  (@ai-sdk/react)│  │  (Generative UI)│  │  (Web Speech)   │           │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘           │  │
│  │           │                    │                    │                     │  │
│  │           ▼                    ▼                    ▼                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │  │
│  │  │                      AI Chat Context Provider                       │ │  │
│  │  │  • Conversation state       • Tool handlers                         │ │  │
│  │  │  • Message history          • Patient context                       │ │  │
│  │  │  • Streaming status         • Healthcare actions                    │ │  │
│  │  └─────────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                         │
│                                        ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                     Next.js API Route (/api/ai/chat)                      │  │
│  │  • AI SDK streamText()                                                    │  │
│  │  • Tool definitions                                                       │  │
│  │  • Response streaming                                                     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                         │
└────────────────────────────────────────┼─────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ /ai/conversations│  │ /ai/chat/       │  │ /ai/triage      │                 │
│  │                 │  │ completions     │  │                 │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ /ai/nlp/entities│  │ /ai/knowledge/  │  │ /ai/documentation│                 │
│  │                 │  │ search          │  │ /generate       │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           FHIR Endpoints                                  │  │
│  │  /fhir/Patient  /fhir/Appointment  /fhir/Slot  /fhir/Practitioner        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (Text/Voice)
        │
        ▼
┌───────────────────┐
│ useChat sendMessage│ ──────────┐
└───────────────────┘            │
                                 ▼
                    ┌──────────────────────┐
                    │ Next.js API Route    │
                    │ /api/ai/chat         │
                    └──────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        ┌───────────────────┐    ┌───────────────────┐
        │ AI Provider       │    │ Tool Execution    │
        │ (Anthropic/OpenAI)│    │ (Backend APIs)    │
        └───────────────────┘    └───────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │ Streaming Response   │
                    │ (Text + Tool Results)│
                    └──────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │ UI Update            │
                    │ (Messages + Cards)   │
                    └──────────────────────┘
```

---

## 2. Backend API Alignment

### Conversation Types (from backend schemas)

| Type | Frontend Use Case |
|------|-------------------|
| `general_inquiry` | Default chat, general questions |
| `appointment_booking` | Book, reschedule, cancel appointments |
| `symptom_assessment` | AI-powered triage flow |
| `medication_question` | Drug info, interactions, side effects |
| `billing_inquiry` | Bill payment, insurance questions |
| `prescription_refill` | Request prescription refills |
| `lab_results` | Query and explain lab results |
| `provider_message` | Provider-initiated communication |

### Backend API → Frontend Tool Mapping

| Backend Endpoint | Frontend Tool Name | UI Component |
|------------------|-------------------|--------------|
| `POST /ai/conversations` | `startConversation` | - |
| `POST /ai/conversations/{id}/messages` | `sendMessage` | - |
| `POST /fhir/Appointment` | `bookAppointment` | `BookingPreviewCard` |
| `GET /fhir/Slot` | `findAvailableSlots` | `SlotPickerCard` |
| `GET /fhir/Patient` | `lookupPatient` | `PatientCard` |
| `POST /ai/triage` | `performTriage` | `TriageResultCard` |
| `GET /ai/knowledge/search` | `searchKnowledge` | `KnowledgeCard` |
| `POST /ai/documentation/generate` | `generateNote` | `DocumentPreviewCard` |
| `GET /fhir/Observation` | `getLabResults` | `LabResultsCard` |
| `POST /billing/payments` | `makePayment` | `PaymentCard` |

### Message Structure Alignment

```typescript
// Backend ConversationMessageResponse
interface BackendMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  intent_type?: string;
  intent_confidence?: number;
  created_at: string;
}

// AI SDK Message (frontend)
interface AIMessage {
  id: string;
  role: 'user' | 'assistant';
  parts: MessagePart[];
  metadata?: {
    intent_type?: string;
    intent_confidence?: number;
    conversation_id?: string;
  };
}

// MessagePart types from AI SDK
type MessagePart =
  | { type: 'text'; text: string }
  | { type: 'tool-invocation'; toolInvocationId: string; toolName: string; args: unknown }
  | { type: 'tool-result'; toolInvocationId: string; toolName: string; result: unknown };
```

---

## 3. Project Setup

### Package Installation

```bash
# Core AI SDK packages
npm install @ai-sdk/react @ai-sdk/anthropic ai

# shadcn/ui components (run these)
npx shadcn@latest add button card input dialog sheet badge avatar scroll-area separator tooltip

# Additional dependencies
npm install lucide-react framer-motion zod date-fns

# Voice input
# Uses native Web Speech API - no additional packages needed
```

### Environment Variables

```env
# .env.local
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/prm
```

### Next.js API Route Setup

```typescript
// src/app/api/ai/chat/route.ts
import { anthropic } from '@ai-sdk/anthropic';
import { streamText, convertToModelMessages, tool } from 'ai';
import { z } from 'zod';

export async function POST(req: Request) {
  const { messages, conversationId, patientContext } = await req.json();

  const result = streamText({
    model: anthropic('claude-sonnet-4-20250514'),
    system: buildSystemPrompt(patientContext),
    messages: convertToModelMessages(messages),
    tools: healthcareTools,
    maxSteps: 5, // Allow multi-step tool usage
  });

  return result.toUIMessageStreamResponse({
    messageMetadata: ({ part }) => {
      if (part.type === 'finish') {
        return {
          totalTokens: part.totalUsage?.totalTokens,
          conversationId,
        };
      }
    },
  });
}

function buildSystemPrompt(patientContext?: PatientContext): string {
  let prompt = `You are a helpful AI healthcare assistant for Surya Hospitals. You can:
- Book, reschedule, and cancel appointments
- Answer questions about medications and health
- Help patients check lab results
- Assist with billing inquiries
- Perform symptom triage (with appropriate disclaimers)

Always be empathetic, professional, and HIPAA-conscious.
Never provide medical diagnoses - always recommend consulting a doctor for medical advice.`;

  if (patientContext) {
    prompt += `\n\nCurrent Patient Context:
- Name: ${patientContext.name}
- MRN: ${patientContext.mrn}
- Allergies: ${patientContext.allergies?.join(', ') || 'None recorded'}
- Active Conditions: ${patientContext.conditions?.join(', ') || 'None recorded'}`;
  }

  return prompt;
}
```

---

## 4. Core Components

### Visual Specification - Full Widget

```
COLLAPSED STATE (FAB - Fixed bottom-right):
┌──────────┐
│  🤖 ✨   │  ← 56x56px, blue-600, shadow-lg
│          │     Green dot indicator when available
└──────────┘

EXPANDED STATE (400px wide, 600px tall):
┌──────────────────────────────────────────────────┐
│ 🤖 AI Assistant                    [_] [✕]      │ ← Header: 56px, bg-white, border-b
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌──────────────────────────────────────────────┐│
│ │              WELCOME MESSAGE                 ││ ← If no messages
│ │                                              ││
│ │    👋 Hello! I'm your AI assistant.         ││
│ │    How can I help you today?                ││
│ │                                              ││
│ │    Quick Actions:                           ││
│ │    ┌─────────────┐ ┌─────────────┐          ││
│ │    │ 📅 Book Appt │ │ 💊 Rx Refill │         ││
│ │    └─────────────┘ └─────────────┘          ││
│ │    ┌─────────────┐ ┌─────────────┐          ││
│ │    │ 🔬 Lab Results│ │ 💳 Pay Bill │         ││
│ │    └─────────────┘ └─────────────┘          ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│ ── OR WITH MESSAGES ──                          │
│                                                  │
│ ┌──────────────────────────────────────────────┐│
│ │                                              ││ ← ScrollArea: flex-1, p-4
│ │ ┌─────────────────────────────────────────┐ ││
│ │ │ 🤖 How can I help you today?            │ ││
│ │ └─────────────────────────────────────────┘ ││
│ │                                              ││
│ │                    ┌────────────────────────┐││
│ │                    │ I'd like to book an   │││ ← User message: bg-blue-600
│ │                    │ appointment with      │││    text-white, rounded-2xl
│ │                    │ Dr. Sharma            │││    rounded-br-sm
│ │                    └────────────────────────┘││
│ │                                              ││
│ │ ┌─────────────────────────────────────────┐ ││
│ │ │ 🤖 I'll help you book an appointment   │ ││ ← Assistant: bg-gray-100
│ │ │ with Dr. Rohit Sharma. Let me find     │ ││    rounded-2xl, rounded-bl-sm
│ │ │ available slots...                     │ ││
│ │ │                                         │ ││
│ │ │ ┌─────────────────────────────────────┐│ ││
│ │ │ │ ⏳ Finding available slots...       ││ ││ ← Tool loading state
│ │ │ │ ████████░░░░░░░                     ││ ││
│ │ │ └─────────────────────────────────────┘│ ││
│ │ └─────────────────────────────────────────┘ ││
│ │                                              ││
│ │ ┌─────────────────────────────────────────┐ ││
│ │ │ 🤖 Here are the available slots:       │ ││
│ │ │                                         │ ││
│ │ │ ┌─────────────────────────────────────┐│ ││
│ │ │ │ 📅 AVAILABLE SLOTS                  ││ ││ ← Tool result card
│ │ │ │ Dr. Rohit Sharma - Cardiology       ││ ││
│ │ │ │                                     ││ ││
│ │ │ │ Tomorrow, Nov 27                    ││ ││
│ │ │ │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   ││ ││
│ │ │ │ │ 9AM │ │10AM │ │11AM │ │ 2PM │   ││ ││
│ │ │ │ └─────┘ └─────┘ └─────┘ └─────┘   ││ ││
│ │ │ │                                     ││ ││
│ │ │ │ Friday, Nov 29                      ││ ││
│ │ │ │ ┌─────┐ ┌─────┐                    ││ ││
│ │ │ │ │10AM │ │ 3PM │                    ││ ││
│ │ │ │ └─────┘ └─────┘                    ││ ││
│ │ │ │                                     ││ ││
│ │ │ │ [View More Dates]                   ││ ││
│ │ │ └─────────────────────────────────────┘│ ││
│ │ └─────────────────────────────────────────┘ ││
│ │                                              ││
│ └──────────────────────────────────────────────┘│
│                                                  │
├──────────────────────────────────────────────────┤
│ Suggestions:                                     │ ← Quick suggestions: py-2
│ [📅 Book] [💊 Refill] [🔬 Labs] [💳 Pay]        │    overflow-x-scroll
├──────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐│
│ │ Ask anything...              [🎤] [⏹️] [➤] ││ ← Input area: p-4
│ └──────────────────────────────────────────────┘│    bg-gray-50, rounded-lg
│                                                  │
│ Press ⌘K anywhere to open                       │ ← Helper text: text-xs
└──────────────────────────────────────────────────┘
```

### Voice Input States

```
IDLE STATE:
┌──────────────────────────────────────────────┐
│ Ask anything...                    [🎤] [➤] │
└──────────────────────────────────────────────┘

LISTENING STATE (animated):
┌──────────────────────────────────────────────┐
│                                              │
│        🎤 Listening...                       │  ← Red pulsing mic icon
│        ████ ██ ████ ██ ████                 │  ← Audio waveform animation
│                                              │
│        Tap to stop                           │
│                                              │
└──────────────────────────────────────────────┘

PROCESSING STATE:
┌──────────────────────────────────────────────┐
│ "Book an appointment with..."       [⏳] [➤] │
└──────────────────────────────────────────────┘
```

---

## 5. AI Tools & Generative UI

### Tool Definitions

```typescript
// src/lib/ai/tools.ts
import { tool } from 'ai';
import { z } from 'zod';

export const healthcareTools = {
  // Appointment Booking
  findAvailableSlots: tool({
    description: 'Find available appointment slots for a practitioner',
    parameters: z.object({
      practitionerId: z.string().optional().describe('Practitioner FHIR ID'),
      practitionerName: z.string().optional().describe('Doctor name to search'),
      specialty: z.string().optional().describe('Medical specialty'),
      dateFrom: z.string().describe('Start date (YYYY-MM-DD)'),
      dateTo: z.string().optional().describe('End date (YYYY-MM-DD)'),
      appointmentType: z.enum(['in-person', 'telehealth', 'any']).default('any'),
    }),
    execute: async ({ practitionerId, practitionerName, specialty, dateFrom, dateTo, appointmentType }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/fhir/Slot`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          practitioner_id: practitionerId,
          practitioner_name: practitionerName,
          specialty,
          start: dateFrom,
          end: dateTo || dateFrom,
          status: 'free',
        }),
      });
      return response.json();
    },
  }),

  bookAppointment: tool({
    description: 'Book an appointment for a patient',
    parameters: z.object({
      patientId: z.string().describe('Patient FHIR ID'),
      slotId: z.string().describe('Selected slot ID'),
      appointmentType: z.string().describe('Type of appointment'),
      reasonForVisit: z.string().optional().describe('Reason for the visit'),
    }),
    execute: async ({ patientId, slotId, appointmentType, reasonForVisit }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/fhir/Appointment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resourceType: 'Appointment',
          status: 'booked',
          slot: [{ reference: `Slot/${slotId}` }],
          participant: [
            { actor: { reference: `Patient/${patientId}` }, status: 'accepted' }
          ],
          appointmentType: { coding: [{ code: appointmentType }] },
          reasonCode: reasonForVisit ? [{ text: reasonForVisit }] : undefined,
        }),
      });
      return response.json();
    },
  }),

  // Patient Lookup
  lookupPatient: tool({
    description: 'Look up a patient by name, phone number, or MRN',
    parameters: z.object({
      searchTerm: z.string().describe('Name, phone, or MRN to search'),
      searchType: z.enum(['name', 'phone', 'mrn', 'auto']).default('auto'),
    }),
    execute: async ({ searchTerm, searchType }) => {
      const params = new URLSearchParams();
      if (searchType === 'auto') {
        // Detect type from format
        if (/^\d{5,}$/.test(searchTerm)) params.set('identifier', searchTerm);
        else if (/^\+?\d{10,}$/.test(searchTerm)) params.set('telecom', searchTerm);
        else params.set('name', searchTerm);
      } else {
        const paramMap = { name: 'name', phone: 'telecom', mrn: 'identifier' };
        params.set(paramMap[searchType], searchTerm);
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/fhir/Patient?${params.toString()}`
      );
      return response.json();
    },
  }),

  // Symptom Triage
  performTriage: tool({
    description: 'Perform AI-powered symptom triage assessment',
    parameters: z.object({
      symptoms: z.array(z.object({
        name: z.string(),
        severity: z.number().min(1).max(10),
        duration: z.string().optional(),
        description: z.string().optional(),
      })),
      patientAge: z.number().optional(),
      patientSex: z.enum(['M', 'F', 'Other']).optional(),
      medicalHistory: z.array(z.string()).optional(),
    }),
    execute: async (params) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ai/triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      return response.json();
    },
  }),

  // Lab Results
  getLabResults: tool({
    description: 'Get lab results for a patient',
    parameters: z.object({
      patientId: z.string().describe('Patient FHIR ID'),
      category: z.string().optional().describe('Lab category filter'),
      dateFrom: z.string().optional().describe('Results from date'),
    }),
    execute: async ({ patientId, category, dateFrom }) => {
      const params = new URLSearchParams({
        patient: patientId,
        _sort: '-date',
        _count: '10',
      });
      if (category) params.set('category', category);
      if (dateFrom) params.set('date', `ge${dateFrom}`);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/fhir/Observation?${params.toString()}`
      );
      return response.json();
    },
  }),

  // Knowledge Search
  searchKnowledge: tool({
    description: 'Search medical knowledge base for information',
    parameters: z.object({
      query: z.string().describe('Search query'),
      documentTypes: z.array(z.string()).optional(),
      maxResults: z.number().default(5),
    }),
    execute: async ({ query, documentTypes, maxResults }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ai/knowledge/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          document_types: documentTypes,
          top_k: maxResults,
        }),
      });
      return response.json();
    },
  }),

  // Billing
  getBillingInfo: tool({
    description: 'Get billing information for a patient',
    parameters: z.object({
      patientId: z.string().describe('Patient ID'),
      includePaymentHistory: z.boolean().default(false),
    }),
    execute: async ({ patientId, includePaymentHistory }) => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/billing/patient/${patientId}/summary`
      );
      return response.json();
    },
  }),
};
```

### Tool Result Components (Generative UI)

```typescript
// src/components/ai-assistant/tool-cards/index.tsx
export { SlotPickerCard } from './slot-picker-card';
export { BookingConfirmationCard } from './booking-confirmation-card';
export { PatientCard } from './patient-card';
export { TriageResultCard } from './triage-result-card';
export { LabResultsCard } from './lab-results-card';
export { KnowledgeCard } from './knowledge-card';
export { BillingCard } from './billing-card';

// src/components/ai-assistant/tool-cards/slot-picker-card.tsx
'use client';

import { format, parseISO, isSameDay } from 'date-fns';
import { Calendar, Clock, MapPin, Video } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface Slot {
  id: string;
  start: string;
  end: string;
  status: string;
  serviceType?: string;
  practitioner?: {
    name: string;
    specialty: string;
  };
  location?: {
    name: string;
    address?: string;
  };
}

interface SlotPickerCardProps {
  data: {
    slots: Slot[];
    practitioner?: {
      id: string;
      name: string;
      specialty: string;
      photo?: string;
    };
  };
  onSelectSlot: (slot: Slot) => void;
  selectedSlotId?: string;
}

export function SlotPickerCard({ data, onSelectSlot, selectedSlotId }: SlotPickerCardProps) {
  const { slots, practitioner } = data;

  // Group slots by date
  const slotsByDate = slots.reduce((acc, slot) => {
    const date = format(parseISO(slot.start), 'yyyy-MM-dd');
    if (!acc[date]) acc[date] = [];
    acc[date].push(slot);
    return acc;
  }, {} as Record<string, Slot[]>);

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-blue-600" />
          <CardTitle className="text-sm font-medium text-blue-800">
            Available Slots
          </CardTitle>
        </div>
        {practitioner && (
          <div className="flex items-center gap-2 mt-2">
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-xs font-medium">{practitioner.name[0]}</span>
            </div>
            <div>
              <p className="text-sm font-medium">{practitioner.name}</p>
              <p className="text-xs text-gray-500">{practitioner.specialty}</p>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.entries(slotsByDate).map(([date, dateSlots]) => (
          <div key={date}>
            <p className="text-xs font-medium text-gray-600 mb-2">
              {format(parseISO(date), 'EEEE, MMMM d')}
            </p>
            <div className="flex flex-wrap gap-2">
              {dateSlots.map((slot) => {
                const isSelected = slot.id === selectedSlotId;
                const isTelehealth = slot.serviceType === 'telehealth';

                return (
                  <Button
                    key={slot.id}
                    variant={isSelected ? 'default' : 'outline'}
                    size="sm"
                    className={cn(
                      'h-8 text-xs',
                      isSelected && 'ring-2 ring-blue-500 ring-offset-1'
                    )}
                    onClick={() => onSelectSlot(slot)}
                  >
                    {isTelehealth && <Video className="h-3 w-3 mr-1" />}
                    {format(parseISO(slot.start), 'h:mm a')}
                  </Button>
                );
              })}
            </div>
          </div>
        ))}

        {slots.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">
            No available slots found. Try different dates.
          </p>
        )}

        <Button variant="ghost" size="sm" className="w-full text-xs">
          View more dates
        </Button>
      </CardContent>
    </Card>
  );
}
```

```typescript
// src/components/ai-assistant/tool-cards/triage-result-card.tsx
'use client';

import { AlertTriangle, CheckCircle, Clock, Phone, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

interface TriageResult {
  triage_id: string;
  urgency_level: 'emergency' | 'urgent' | 'soon' | 'routine' | 'self_care';
  urgency_score: number;
  primary_concern: string;
  red_flags_identified: string[];
  recommended_action: string;
  timeframe: string;
  care_setting: string;
  self_care_advice: string[];
  warning_signs: string[];
  confidence_score: number;
  disclaimer: string;
}

interface TriageResultCardProps {
  data: TriageResult;
  onBookAppointment?: () => void;
  onCallEmergency?: () => void;
}

const urgencyConfig = {
  emergency: {
    color: 'bg-red-100 text-red-800 border-red-300',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    label: 'Emergency',
  },
  urgent: {
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: AlertTriangle,
    iconColor: 'text-orange-600',
    label: 'Urgent',
  },
  soon: {
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    icon: Clock,
    iconColor: 'text-yellow-600',
    label: 'Seek Care Soon',
  },
  routine: {
    color: 'bg-green-100 text-green-800 border-green-300',
    icon: CheckCircle,
    iconColor: 'text-green-600',
    label: 'Routine',
  },
  self_care: {
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: Info,
    iconColor: 'text-blue-600',
    label: 'Self Care',
  },
};

export function TriageResultCard({ data, onBookAppointment, onCallEmergency }: TriageResultCardProps) {
  const config = urgencyConfig[data.urgency_level];
  const UrgencyIcon = config.icon;

  return (
    <Card className={cn('border-2', config.color.split(' ').pop())}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UrgencyIcon className={cn('h-5 w-5', config.iconColor)} />
            <CardTitle className="text-sm font-medium">
              Triage Assessment
            </CardTitle>
          </div>
          <Badge className={config.color}>{config.label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Primary Concern */}
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase">Primary Concern</p>
          <p className="text-sm font-medium">{data.primary_concern}</p>
        </div>

        {/* Red Flags */}
        {data.red_flags_identified.length > 0 && (
          <Alert variant="destructive" className="py-2">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              <strong>Warning Signs Detected:</strong>
              <ul className="list-disc list-inside mt-1">
                {data.red_flags_identified.map((flag, i) => (
                  <li key={i}>{flag}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Recommendation */}
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Recommendation</p>
          <p className="text-sm">{data.recommended_action}</p>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
            <span>⏱️ {data.timeframe}</span>
            <span>🏥 {data.care_setting}</span>
          </div>
        </div>

        {/* Self Care Advice */}
        {data.self_care_advice.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase mb-1">Self Care Advice</p>
            <ul className="text-xs text-gray-700 space-y-1">
              {data.self_care_advice.map((advice, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span>•</span> {advice}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t">
          {data.urgency_level === 'emergency' ? (
            <Button
              variant="destructive"
              className="flex-1"
              onClick={onCallEmergency}
            >
              <Phone className="h-4 w-4 mr-2" />
              Call Emergency (112)
            </Button>
          ) : (
            <Button
              variant="default"
              className="flex-1"
              onClick={onBookAppointment}
            >
              Book Appointment
            </Button>
          )}
        </div>

        {/* Disclaimer */}
        <p className="text-[10px] text-gray-400 italic">
          {data.disclaimer}
        </p>

        {/* Confidence */}
        <div className="flex items-center gap-1 text-[10px] text-gray-400">
          <span>Confidence:</span>
          <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full"
              style={{ width: `${data.confidence_score * 100}%` }}
            />
          </div>
          <span>{Math.round(data.confidence_score * 100)}%</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Tool Result Renderer

```typescript
// src/components/ai-assistant/tool-result-renderer.tsx
'use client';

import { Loader2 } from 'lucide-react';
import {
  SlotPickerCard,
  BookingConfirmationCard,
  PatientCard,
  TriageResultCard,
  LabResultsCard,
  KnowledgeCard,
  BillingCard,
} from './tool-cards';
import { useAIAssistant } from './ai-assistant-provider';

interface ToolResultRendererProps {
  toolName: string;
  toolInvocationId: string;
  state: 'input-available' | 'output-available' | 'output-error';
  args?: Record<string, unknown>;
  result?: unknown;
  error?: string;
}

export function ToolResultRenderer({
  toolName,
  toolInvocationId,
  state,
  args,
  result,
  error,
}: ToolResultRendererProps) {
  const { handleToolAction } = useAIAssistant();

  // Loading state
  if (state === 'input-available') {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500 bg-gray-50 rounded-lg p-3">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>{getLoadingMessage(toolName, args)}</span>
      </div>
    );
  }

  // Error state
  if (state === 'output-error') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
        <p className="font-medium">Something went wrong</p>
        <p className="text-xs mt-1">{error || 'Failed to complete the action'}</p>
      </div>
    );
  }

  // Success state - render appropriate card
  switch (toolName) {
    case 'findAvailableSlots':
      return (
        <SlotPickerCard
          data={result as any}
          onSelectSlot={(slot) => handleToolAction('selectSlot', { slot })}
        />
      );

    case 'bookAppointment':
      return <BookingConfirmationCard data={result as any} />;

    case 'lookupPatient':
      return (
        <PatientCard
          data={result as any}
          onSelectPatient={(patient) => handleToolAction('selectPatient', { patient })}
        />
      );

    case 'performTriage':
      return (
        <TriageResultCard
          data={result as any}
          onBookAppointment={() => handleToolAction('bookFromTriage', { triageId: (result as any).triage_id })}
        />
      );

    case 'getLabResults':
      return <LabResultsCard data={result as any} />;

    case 'searchKnowledge':
      return <KnowledgeCard data={result as any} />;

    case 'getBillingInfo':
      return (
        <BillingCard
          data={result as any}
          onPayBill={() => handleToolAction('payBill', { patientId: args?.patientId })}
        />
      );

    default:
      // Generic JSON display for unknown tools
      return (
        <pre className="bg-gray-50 rounded-lg p-3 text-xs overflow-auto max-h-48">
          {JSON.stringify(result, null, 2)}
        </pre>
      );
  }
}

function getLoadingMessage(toolName: string, args?: Record<string, unknown>): string {
  switch (toolName) {
    case 'findAvailableSlots':
      return 'Finding available appointment slots...';
    case 'bookAppointment':
      return 'Booking your appointment...';
    case 'lookupPatient':
      return `Searching for patient "${args?.searchTerm}"...`;
    case 'performTriage':
      return 'Analyzing symptoms...';
    case 'getLabResults':
      return 'Retrieving lab results...';
    case 'searchKnowledge':
      return 'Searching medical knowledge base...';
    case 'getBillingInfo':
      return 'Loading billing information...';
    default:
      return 'Processing...';
  }
}
```

---

## 6. Voice Input Integration

### Web Speech API Implementation

```typescript
// src/hooks/use-voice-input.ts
'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface UseVoiceInputOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
}

interface UseVoiceInputReturn {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  interimTranscript: string;
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  resetTranscript: () => void;
}

export function useVoiceInput({
  language = 'en-US',
  continuous = false,
  interimResults = true,
  onResult,
  onError,
  onStart,
  onEnd,
}: UseVoiceInputOptions = {}): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check for browser support
  const isSupported = typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  // Initialize recognition
  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = language;
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;

    recognition.onstart = () => {
      setIsListening(true);
      onStart?.();
    };

    recognition.onend = () => {
      setIsListening(false);
      onEnd?.();
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      const errorMessage = getErrorMessage(event.error);
      onError?.(errorMessage);
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interim = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (finalTranscript) {
        setTranscript((prev) => prev + finalTranscript);
        onResult?.(finalTranscript, true);
      }

      setInterimTranscript(interim);
      if (interim) {
        onResult?.(interim, false);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, [language, continuous, interimResults, isSupported, onResult, onError, onStart, onEnd]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current || isListening) return;

    setTranscript('');
    setInterimTranscript('');

    try {
      recognitionRef.current.start();
    } catch (error) {
      // Already started
    }
  }, [isListening]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) return;
    recognitionRef.current.stop();
  }, [isListening]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  return {
    isListening,
    isSupported,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    toggleListening,
    resetTranscript,
  };
}

function getErrorMessage(error: string): string {
  switch (error) {
    case 'no-speech':
      return 'No speech was detected. Please try again.';
    case 'audio-capture':
      return 'No microphone was found. Please check your device.';
    case 'not-allowed':
      return 'Microphone permission denied. Please allow access.';
    case 'network':
      return 'Network error occurred. Please check your connection.';
    default:
      return 'An error occurred with voice recognition.';
  }
}

// Type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
```

### Voice Input Component

```typescript
// src/components/ai-assistant/voice-input.tsx
'use client';

import { useState, useEffect } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useVoiceInput } from '@/hooks/use-voice-input';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  className?: string;
}

export function VoiceInput({ onTranscript, disabled, className }: VoiceInputProps) {
  const [showPermissionToast, setShowPermissionToast] = useState(false);

  const {
    isListening,
    isSupported,
    transcript,
    interimTranscript,
    toggleListening,
    resetTranscript,
  } = useVoiceInput({
    language: 'en-US',
    continuous: false,
    interimResults: true,
    onResult: (text, isFinal) => {
      if (isFinal) {
        onTranscript(text);
        resetTranscript();
      }
    },
    onError: (error) => {
      if (error.includes('permission')) {
        setShowPermissionToast(true);
      }
    },
  });

  if (!isSupported) {
    return null; // Don't show mic button if not supported
  }

  return (
    <div className={cn('relative', className)}>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={toggleListening}
        disabled={disabled}
        className={cn(
          'h-9 w-9 rounded-full transition-all',
          isListening && 'bg-red-100 text-red-600 animate-pulse'
        )}
      >
        {isListening ? (
          <MicOff className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>

      {/* Listening indicator */}
      {isListening && (
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-1.5 rounded-full whitespace-nowrap">
          <div className="flex items-center gap-2">
            <span className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map((i) => (
                <span
                  key={i}
                  className="w-0.5 bg-white rounded-full animate-pulse"
                  style={{
                    height: `${8 + Math.random() * 8}px`,
                    animationDelay: `${i * 0.1}s`,
                  }}
                />
              ))}
            </span>
            <span>Listening...</span>
          </div>
        </div>
      )}

      {/* Interim transcript preview */}
      {interimTranscript && (
        <div className="absolute bottom-full left-0 right-0 mb-2 p-2 bg-gray-100 rounded-lg text-xs text-gray-600 italic">
          {interimTranscript}
        </div>
      )}
    </div>
  );
}
```

---

## 7. State Management

### AI Assistant Store (Zustand)

```typescript
// src/stores/ai-assistant-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PatientContext {
  id: string;
  name: string;
  mrn: string;
  dateOfBirth?: string;
  allergies?: string[];
  conditions?: string[];
}

interface AIAssistantState {
  // Widget state
  isOpen: boolean;
  isMinimized: boolean;

  // Conversation
  conversationId: string | null;
  conversationType: string | null;

  // Context
  patientContext: PatientContext | null;
  pageContext: Record<string, unknown>;

  // Actions
  setOpen: (open: boolean) => void;
  setMinimized: (minimized: boolean) => void;
  setConversationId: (id: string | null) => void;
  setConversationType: (type: string | null) => void;
  setPatientContext: (patient: PatientContext | null) => void;
  setPageContext: (context: Record<string, unknown>) => void;
  clearConversation: () => void;
}

export const useAIAssistantStore = create<AIAssistantState>()(
  persist(
    (set) => ({
      // Initial state
      isOpen: false,
      isMinimized: false,
      conversationId: null,
      conversationType: null,
      patientContext: null,
      pageContext: {},

      // Actions
      setOpen: (open) => set({ isOpen: open }),
      setMinimized: (minimized) => set({ isMinimized: minimized }),
      setConversationId: (id) => set({ conversationId: id }),
      setConversationType: (type) => set({ conversationType: type }),
      setPatientContext: (patient) => set({ patientContext: patient }),
      setPageContext: (context) => set({ pageContext: context }),
      clearConversation: () => set({
        conversationId: null,
        conversationType: null
      }),
    }),
    {
      name: 'ai-assistant-storage',
      partialize: (state) => ({
        // Only persist these fields
        conversationId: state.conversationId,
      }),
    }
  )
);
```

### AI Assistant Context Provider

```typescript
// src/components/ai-assistant/ai-assistant-provider.tsx
'use client';

import React, { createContext, useContext, useCallback, useMemo } from 'react';
import { useChat, type Message } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useAIAssistantStore } from '@/stores/ai-assistant-store';

interface AIAssistantContextValue {
  // Chat state from AI SDK
  messages: Message[];
  status: 'submitted' | 'streaming' | 'ready' | 'error';
  error: Error | null;

  // Actions
  sendMessage: (content: string, options?: SendMessageOptions) => void;
  stop: () => void;
  regenerate: () => void;
  clearMessages: () => void;

  // Tool action handler
  handleToolAction: (action: string, data: Record<string, unknown>) => void;

  // Context
  patientContext: PatientContext | null;
  setPatientContext: (patient: PatientContext | null) => void;
}

interface SendMessageOptions {
  metadata?: Record<string, unknown>;
}

const AIAssistantContext = createContext<AIAssistantContextValue | null>(null);

export function AIAssistantProvider({ children }: { children: React.ReactNode }) {
  const {
    conversationId,
    patientContext,
    setConversationId,
    setPatientContext,
  } = useAIAssistantStore();

  const {
    messages,
    sendMessage: sdkSendMessage,
    status,
    error,
    stop,
    setMessages,
  } = useChat({
    transport: new DefaultChatTransport({
      api: '/api/ai/chat',
      headers: {
        'X-Conversation-Id': conversationId || '',
      },
    }),
    onFinish: ({ message }) => {
      // Extract conversation ID from response metadata if new conversation
      if (message.metadata?.conversationId && !conversationId) {
        setConversationId(message.metadata.conversationId as string);
      }
    },
    experimental_throttle: 50, // Throttle UI updates for smoother rendering
  });

  // Send message with patient context
  const sendMessage = useCallback((content: string, options?: SendMessageOptions) => {
    sdkSendMessage(
      { text: content },
      {
        body: {
          conversationId,
          patientContext,
          ...options?.metadata,
        },
      }
    );
  }, [sdkSendMessage, conversationId, patientContext]);

  // Regenerate last assistant message
  const regenerate = useCallback(() => {
    const lastUserMessageIndex = [...messages].reverse().findIndex(m => m.role === 'user');
    if (lastUserMessageIndex === -1) return;

    const lastUserMessage = messages[messages.length - 1 - lastUserMessageIndex];
    const userText = lastUserMessage.parts.find(p => p.type === 'text')?.text;

    if (userText) {
      // Remove messages after last user message and resend
      const newMessages = messages.slice(0, messages.length - lastUserMessageIndex);
      setMessages(newMessages);
      sendMessage(userText);
    }
  }, [messages, setMessages, sendMessage]);

  // Clear all messages
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, [setMessages, setConversationId]);

  // Handle tool-specific actions (e.g., selecting a slot from SlotPickerCard)
  const handleToolAction = useCallback((action: string, data: Record<string, unknown>) => {
    switch (action) {
      case 'selectSlot':
        // Send a message that the user selected a slot
        sendMessage(`I'd like to book the ${data.slot.start} slot`, {
          metadata: { selectedSlot: data.slot },
        });
        break;

      case 'selectPatient':
        // Set patient context
        setPatientContext(data.patient as PatientContext);
        sendMessage(`Selected patient ${data.patient.name}`, {
          metadata: { selectedPatient: data.patient },
        });
        break;

      case 'bookFromTriage':
        sendMessage('Please help me book an appointment based on this triage assessment', {
          metadata: { triageId: data.triageId },
        });
        break;

      case 'payBill':
        sendMessage('I want to proceed with paying my bill', {
          metadata: { patientId: data.patientId },
        });
        break;

      default:
        console.warn(`Unknown tool action: ${action}`);
    }
  }, [sendMessage, setPatientContext]);

  const value = useMemo(() => ({
    messages,
    status,
    error,
    sendMessage,
    stop,
    regenerate,
    clearMessages,
    handleToolAction,
    patientContext,
    setPatientContext,
  }), [
    messages,
    status,
    error,
    sendMessage,
    stop,
    regenerate,
    clearMessages,
    handleToolAction,
    patientContext,
    setPatientContext,
  ]);

  return (
    <AIAssistantContext.Provider value={value}>
      {children}
    </AIAssistantContext.Provider>
  );
}

export function useAIAssistant() {
  const context = useContext(AIAssistantContext);
  if (!context) {
    throw new Error('useAIAssistant must be used within AIAssistantProvider');
  }
  return context;
}
```

---

## 8. Visual Specifications

### Color Tokens

```css
/* src/styles/ai-assistant.css */

/* Widget Container */
.ai-widget {
  --ai-bg: theme('colors.white');
  --ai-border: theme('colors.gray.200');
  --ai-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
}

/* User Messages */
.ai-user-message {
  --ai-user-bg: theme('colors.blue.600');
  --ai-user-text: theme('colors.white');
  --ai-user-radius: 1rem 1rem 0.25rem 1rem; /* rounded-br-sm */
}

/* Assistant Messages */
.ai-assistant-message {
  --ai-assistant-bg: theme('colors.gray.100');
  --ai-assistant-text: theme('colors.gray.900');
  --ai-assistant-radius: 1rem 1rem 1rem 0.25rem; /* rounded-bl-sm */
}

/* Tool Cards */
.ai-tool-card {
  --ai-card-bg: theme('colors.blue.50/30');
  --ai-card-border: theme('colors.blue.200');
  --ai-card-header: theme('colors.blue.800');
}

/* Status Colors */
.ai-status-streaming {
  --ai-status-color: theme('colors.blue.500');
}

.ai-status-error {
  --ai-status-color: theme('colors.red.500');
}

/* Voice Input */
.ai-voice-listening {
  --ai-voice-bg: theme('colors.red.100');
  --ai-voice-color: theme('colors.red.600');
  --ai-voice-pulse: theme('animation.pulse');
}
```

### Animation Specifications

```typescript
// Framer Motion variants for animations
export const messageVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.2, ease: 'easeOut' }
  },
};

export const widgetVariants = {
  collapsed: {
    scale: 0.9,
    opacity: 0,
    transition: { duration: 0.15 }
  },
  expanded: {
    scale: 1,
    opacity: 1,
    transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] }
  },
};

export const fabVariants = {
  idle: { scale: 1 },
  hover: { scale: 1.05 },
  tap: { scale: 0.95 },
};

export const typingIndicatorVariants = {
  animate: {
    opacity: [0.4, 1, 0.4],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};
```

### Responsive Breakpoints

```
Mobile (< 640px):
- Widget takes full screen when open
- FAB: 48x48px, bottom-right with 16px margin
- No minimize, only close

Tablet (640px - 1024px):
- Widget: 380px wide, 500px tall
- FAB: 56x56px, bottom-right with 24px margin

Desktop (> 1024px):
- Widget: 400px wide, 600px tall
- FAB: 56x56px, bottom-right with 24px margin
- Can be docked to right side
```

---

## 9. File Structure

```
src/
├── app/
│   ├── api/
│   │   └── ai/
│   │       └── chat/
│   │           └── route.ts              # AI chat API endpoint
│   └── layout.tsx                        # Include AIAssistantProvider
│
├── components/
│   └── ai-assistant/
│       ├── index.ts                      # Export barrel
│       ├── ai-assistant-widget.tsx       # Main widget component
│       ├── ai-assistant-provider.tsx     # Context provider
│       ├── chat-message.tsx              # Message component
│       ├── chat-message-list.tsx         # Message list with scroll
│       ├── chat-input.tsx                # Input with voice toggle
│       ├── voice-input.tsx               # Voice input component
│       ├── typing-indicator.tsx          # Streaming indicator
│       ├── quick-actions.tsx             # Suggestion chips
│       ├── welcome-screen.tsx            # Initial welcome state
│       ├── tool-result-renderer.tsx      # Tool result dispatcher
│       └── tool-cards/
│           ├── index.ts
│           ├── slot-picker-card.tsx
│           ├── booking-confirmation-card.tsx
│           ├── patient-card.tsx
│           ├── triage-result-card.tsx
│           ├── lab-results-card.tsx
│           ├── knowledge-card.tsx
│           └── billing-card.tsx
│
├── hooks/
│   ├── use-voice-input.ts               # Web Speech API hook
│   └── use-keyboard-shortcut.ts         # ⌘K shortcut hook
│
├── lib/
│   └── ai/
│       ├── tools.ts                     # Tool definitions
│       └── prompts.ts                   # System prompts
│
├── stores/
│   └── ai-assistant-store.ts            # Zustand store
│
└── styles/
    └── ai-assistant.css                 # Widget-specific styles
```

---

## 10. Complete Component Code

### Main Widget Component

```typescript
// src/components/ai-assistant/ai-assistant-widget.tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, X, Minimize2, Maximize2, RotateCcw, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useAIAssistant } from './ai-assistant-provider';
import { useAIAssistantStore } from '@/stores/ai-assistant-store';
import { ChatMessageList } from './chat-message-list';
import { ChatInput } from './chat-input';
import { WelcomeScreen } from './welcome-screen';
import { QuickActions } from './quick-actions';

export function AIAssistantWidget() {
  const { isOpen, isMinimized, setOpen, setMinimized } = useAIAssistantStore();
  const { messages, status, clearMessages, regenerate } = useAIAssistant();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Keyboard shortcut: ⌘K to toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(!isOpen);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, setOpen]);

  // FAB (Floating Action Button) when closed
  if (!isOpen) {
    return (
      <motion.button
        onClick={() => setOpen(true)}
        className={cn(
          'fixed bottom-6 right-6 z-50',
          'h-14 w-14 rounded-full',
          'bg-blue-600 hover:bg-blue-700 text-white',
          'shadow-lg hover:shadow-xl',
          'flex items-center justify-center',
          'transition-colors duration-200'
        )}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Bot className="h-6 w-6" />
        {/* Online indicator */}
        <span className="absolute -top-0.5 -right-0.5 h-3.5 w-3.5 bg-green-500 rounded-full border-2 border-white" />
      </motion.button>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        className={cn(
          'fixed bottom-6 right-6 z-50',
          'w-[400px] bg-white rounded-2xl shadow-2xl',
          'border border-gray-200',
          'flex flex-col overflow-hidden',
          isMinimized ? 'h-14' : 'h-[600px]'
        )}
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2 }}
      >
        {/* Header */}
        <div className="h-14 px-4 flex items-center justify-between border-b border-gray-100 bg-white">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
              <Bot className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <span className="font-semibold text-sm">AI Assistant</span>
              {status === 'streaming' && (
                <span className="ml-2 text-xs text-blue-600">typing...</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {/* Regenerate button */}
            {messages.length > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={regenerate}
                    disabled={status === 'streaming'}
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Regenerate response</TooltipContent>
              </Tooltip>
            )}

            {/* Clear button */}
            {messages.length > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={clearMessages}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Clear conversation</TooltipContent>
              </Tooltip>
            )}

            {/* Minimize button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setMinimized(!isMinimized)}
            >
              {isMinimized ? (
                <Maximize2 className="h-4 w-4" />
              ) : (
                <Minimize2 className="h-4 w-4" />
              )}
            </Button>

            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Body (hidden when minimized) */}
        {!isMinimized && (
          <>
            {/* Messages Area */}
            <ScrollArea
              ref={scrollRef}
              className="flex-1 p-4"
            >
              {messages.length === 0 ? (
                <WelcomeScreen />
              ) : (
                <ChatMessageList messages={messages} />
              )}
            </ScrollArea>

            {/* Quick Actions */}
            <QuickActions />

            {/* Input Area */}
            <ChatInput />

            {/* Keyboard hint */}
            <div className="px-4 pb-2">
              <p className="text-[10px] text-gray-400 text-center">
                Press{' '}
                <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[9px] font-mono">
                  ⌘K
                </kbd>{' '}
                anywhere to toggle
              </p>
            </div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
```

### Chat Message List

```typescript
// src/components/ai-assistant/chat-message-list.tsx
'use client';

import { motion } from 'framer-motion';
import { type Message } from '@ai-sdk/react';
import { ChatMessage } from './chat-message';
import { TypingIndicator } from './typing-indicator';
import { useAIAssistant } from './ai-assistant-provider';

interface ChatMessageListProps {
  messages: Message[];
}

export function ChatMessageList({ messages }: ChatMessageListProps) {
  const { status } = useAIAssistant();

  return (
    <div className="space-y-4">
      {messages.map((message, index) => (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <ChatMessage message={message} />
        </motion.div>
      ))}

      {status === 'submitted' && <TypingIndicator />}
    </div>
  );
}
```

### Chat Message Component

```typescript
// src/components/ai-assistant/chat-message.tsx
'use client';

import { type Message } from '@ai-sdk/react';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToolResultRenderer } from './tool-result-renderer';
import { format } from 'date-fns';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'h-8 w-8 rounded-full flex items-center justify-center shrink-0',
          isUser ? 'bg-blue-600' : 'bg-gray-100'
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-gray-600" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('max-w-[85%] space-y-2', isUser && 'text-right')}>
        {message.parts.map((part, index) => {
          // Text part
          if (part.type === 'text') {
            return (
              <div
                key={index}
                className={cn(
                  'px-4 py-2.5 rounded-2xl text-sm',
                  isUser
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-gray-100 text-gray-900 rounded-bl-sm'
                )}
              >
                {part.text}
              </div>
            );
          }

          // Tool invocation (loading state)
          if (part.type === 'tool-invocation') {
            return (
              <ToolResultRenderer
                key={index}
                toolName={part.toolName}
                toolInvocationId={part.toolInvocationId}
                state="input-available"
                args={part.args}
              />
            );
          }

          // Tool result
          if (part.type === 'tool-result') {
            return (
              <ToolResultRenderer
                key={index}
                toolName={part.toolName}
                toolInvocationId={part.toolInvocationId}
                state={part.isError ? 'output-error' : 'output-available'}
                result={part.result}
                error={part.isError ? String(part.result) : undefined}
              />
            );
          }

          return null;
        })}

        {/* Timestamp */}
        {message.metadata?.createdAt && (
          <span className="text-[10px] text-gray-400">
            {format(new Date(message.metadata.createdAt as string), 'h:mm a')}
          </span>
        )}
      </div>
    </div>
  );
}
```

### Chat Input Component

```typescript
// src/components/ai-assistant/chat-input.tsx
'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { useAIAssistant } from './ai-assistant-provider';
import { VoiceInput } from './voice-input';

export function ChatInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, status, stop } = useAIAssistant();

  const isStreaming = status === 'streaming' || status === 'submitted';

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput('');
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleVoiceTranscript = (text: string) => {
    setInput((prev) => prev + text);
  };

  return (
    <div className="p-4 border-t border-gray-100">
      <div className="flex items-end gap-2 bg-gray-50 rounded-xl p-2">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
          className={cn(
            'min-h-[40px] max-h-[120px] resize-none',
            'border-0 bg-transparent focus-visible:ring-0',
            'text-sm placeholder:text-gray-400'
          )}
          rows={1}
          disabled={isStreaming}
        />

        <div className="flex items-center gap-1 pb-1">
          {/* Voice Input */}
          <VoiceInput
            onTranscript={handleVoiceTranscript}
            disabled={isStreaming}
          />

          {/* Send/Stop Button */}
          {isStreaming ? (
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-full"
              onClick={stop}
            >
              <Loader2 className="h-4 w-4 animate-spin" />
            </Button>
          ) : (
            <Button
              variant="default"
              size="icon"
              className="h-9 w-9 rounded-full"
              onClick={handleSubmit}
              disabled={!input.trim()}
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

### Welcome Screen

```typescript
// src/components/ai-assistant/welcome-screen.tsx
'use client';

import { Calendar, Pill, FlaskConical, CreditCard, MessageSquare, Stethoscope } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAIAssistant } from './ai-assistant-provider';

const quickStarters = [
  { icon: Calendar, label: 'Book Appointment', prompt: 'I want to book an appointment' },
  { icon: Pill, label: 'Refill Prescription', prompt: 'I need to refill my prescription' },
  { icon: FlaskConical, label: 'Lab Results', prompt: 'Show me my recent lab results' },
  { icon: CreditCard, label: 'Pay Bill', prompt: 'I want to pay my bill' },
  { icon: MessageSquare, label: 'Message Doctor', prompt: 'I need to message my doctor' },
  { icon: Stethoscope, label: 'Symptom Check', prompt: 'I have some symptoms I want to check' },
];

export function WelcomeScreen() {
  const { sendMessage } = useAIAssistant();

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="mb-6">
        <div className="text-4xl mb-2">👋</div>
        <h3 className="text-lg font-semibold text-gray-900">
          Hello! I'm your AI assistant.
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          How can I help you today?
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 w-full max-w-xs">
        {quickStarters.map(({ icon: Icon, label, prompt }) => (
          <Button
            key={label}
            variant="outline"
            className="h-auto py-3 px-3 flex flex-col items-center gap-1.5 text-xs hover:bg-blue-50 hover:border-blue-200"
            onClick={() => sendMessage(prompt)}
          >
            <Icon className="h-5 w-5 text-blue-600" />
            <span>{label}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}
```

### Quick Actions (Suggestion Chips)

```typescript
// src/components/ai-assistant/quick-actions.tsx
'use client';

import { Calendar, Pill, FlaskConical, CreditCard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { useAIAssistant } from './ai-assistant-provider';

const suggestions = [
  { icon: Calendar, label: 'Book', prompt: 'I want to book an appointment' },
  { icon: Pill, label: 'Refill', prompt: 'I need a prescription refill' },
  { icon: FlaskConical, label: 'Labs', prompt: 'Show my lab results' },
  { icon: CreditCard, label: 'Pay', prompt: 'I want to pay my bill' },
];

export function QuickActions() {
  const { sendMessage, status } = useAIAssistant();
  const isDisabled = status === 'streaming' || status === 'submitted';

  return (
    <div className="px-4 py-2 border-t border-gray-50">
      <p className="text-[10px] text-gray-400 mb-1.5">Suggestions:</p>
      <ScrollArea className="w-full whitespace-nowrap">
        <div className="flex gap-2">
          {suggestions.map(({ icon: Icon, label, prompt }) => (
            <Button
              key={label}
              variant="outline"
              size="sm"
              className="h-7 px-3 text-xs shrink-0"
              onClick={() => sendMessage(prompt)}
              disabled={isDisabled}
            >
              <Icon className="h-3 w-3 mr-1.5" />
              {label}
            </Button>
          ))}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}
```

### Typing Indicator

```typescript
// src/components/ai-assistant/typing-indicator.tsx
'use client';

import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

export function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
        <Bot className="h-4 w-4 text-gray-600" />
      </div>
      <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="w-2 h-2 bg-gray-400 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Usage in Application

### Layout Integration

```typescript
// src/app/layout.tsx
import { AIAssistantProvider } from '@/components/ai-assistant/ai-assistant-provider';
import { AIAssistantWidget } from '@/components/ai-assistant/ai-assistant-widget';
import { TooltipProvider } from '@/components/ui/tooltip';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <TooltipProvider>
          <AIAssistantProvider>
            {children}
            <AIAssistantWidget />
          </AIAssistantProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
```

### Setting Patient Context from Pages

```typescript
// Example: Setting context when viewing a patient
'use client';

import { useEffect } from 'react';
import { useAIAssistantStore } from '@/stores/ai-assistant-store';

export function PatientPage({ patient }) {
  const setPatientContext = useAIAssistantStore((s) => s.setPatientContext);

  useEffect(() => {
    // Set patient context when page loads
    setPatientContext({
      id: patient.id,
      name: `${patient.name[0].given.join(' ')} ${patient.name[0].family}`,
      mrn: patient.identifier?.find(i => i.type === 'MRN')?.value,
      allergies: patient.allergies?.map(a => a.code.text),
      conditions: patient.conditions?.map(c => c.code.text),
    });

    // Clear on unmount
    return () => setPatientContext(null);
  }, [patient, setPatientContext]);

  return (/* patient page content */);
}
```

---

## Summary

This implementation guide provides:

1. **Full Vercel AI SDK integration** using `useChat` hook with streaming
2. **Tool-based generative UI** for healthcare actions (booking, triage, labs, etc.)
3. **Backend API alignment** with exact schema mappings to FastAPI endpoints
4. **Voice input** using native Web Speech API
5. **Complete component library** with shadcn/ui styling
6. **State management** with Zustand for persistence
7. **TypeScript types** matching backend Pydantic schemas

The widget is designed to be healthcare-specific with proper HIPAA considerations, while maintaining a modern B2B SaaS aesthetic that's clean, professional, and accessible.

---

**Document Owner:** Frontend Architecture Team
**Last Updated:** November 26, 2024
**Review Cycle:** Every Sprint
