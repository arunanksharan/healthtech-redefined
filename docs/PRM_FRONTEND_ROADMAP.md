# PRM Frontend Roadmap

**System:** Patient Relationship Management (PRM) Dashboard
**Target Users:** Hospital staff, administrators, care coordinators
**Date:** November 18, 2024

---

## 🎯 Vision

Build a modern, AI-powered PRM dashboard that enables healthcare staff to manage patient relationships, journeys, appointments, and communications through an intuitive interface with natural language capabilities.

---

## 🏗️ Technical Architecture

### Tech Stack

**Frontend Framework**
- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **React 18+** with Server Components where applicable

**State Management**
- **React Query (TanStack Query)** - Server state management & caching
- **Zustand** - Client state management (UI state, user preferences)

**UI Framework**
- **Shadcn/ui** - Component library built on Radix UI
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Animations & transitions

**Data Visualization**
- **Recharts** - Charts and graphs
- **React Flow** - Journey visualization

**Real-time Communication**
- **WebSocket** - Live updates for messages, appointments, journey changes
- **Server-Sent Events (SSE)** - Alternative for unidirectional updates

**AI Assistant Integration**
- **Chitchat Components** (to be reused from existing chitchat project)
- **Web Speech API** - Voice input
- **Text-to-Speech** - Voice responses
- **Streaming LLM Responses** - Gradual response rendering

**API Communication**
- **Axios** or **fetch** with interceptors
- **OpenAPI TypeScript Generator** - Auto-generate API types from backend OpenAPI spec

---

## 📐 Application Structure

```
prm-frontend/
├── app/                        # Next.js app directory
│   ├── (auth)/                 # Authentication routes
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/            # Main dashboard routes
│   │   ├── layout.tsx          # Dashboard layout with sidebar
│   │   ├── page.tsx            # Dashboard home
│   │   ├── patients/           # Patient management
│   │   │   ├── page.tsx        # Patient list
│   │   │   ├── [id]/           # Patient detail views
│   │   │   │   ├── page.tsx    # Patient 360 view
│   │   │   │   ├── journeys/   # Patient journeys
│   │   │   │   ├── appointments/
│   │   │   │   ├── communications/
│   │   │   │   └── tickets/
│   │   │   └── new/            # Create new patient
│   │   ├── journeys/           # Journey management
│   │   │   ├── page.tsx        # Journey definitions list
│   │   │   ├── [id]/           # Journey detail
│   │   │   └── instances/      # Active journey instances
│   │   ├── appointments/       # Appointment management
│   │   │   ├── page.tsx        # Appointment calendar
│   │   │   ├── [id]/           # Appointment detail
│   │   │   └── schedule/       # Provider schedules
│   │   ├── communications/     # Communication center
│   │   │   ├── page.tsx        # All communications
│   │   │   └── templates/      # Message templates
│   │   ├── tickets/            # Support tickets
│   │   │   ├── page.tsx        # Ticket list
│   │   │   └── [id]/           # Ticket detail
│   │   └── settings/           # System settings
│   └── api/                    # API route handlers (if needed)
├── components/                 # Reusable components
│   ├── ui/                     # Shadcn/ui components
│   ├── layout/                 # Layout components
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   ├── patients/               # Patient-specific components
│   ├── journeys/               # Journey components
│   ├── appointments/           # Appointment components
│   ├── communications/         # Communication components
│   ├── ai-assistant/           # AI assistant components
│   │   ├── ChatInterface.tsx   # Text chat UI
│   │   ├── VoiceInput.tsx      # Voice input button
│   │   ├── CommandParser.tsx   # Natural language command parsing
│   │   └── ActionConfirmation.tsx
│   └── common/                 # Common components
│       ├── DataTable.tsx
│       ├── SearchBar.tsx
│       ├── FilterPanel.tsx
│       └── Charts/
├── lib/                        # Utilities and helpers
│   ├── api/                    # API client
│   │   ├── client.ts           # Axios instance
│   │   ├── patients.ts         # Patient API calls
│   │   ├── journeys.ts
│   │   ├── appointments.ts
│   │   └── communications.ts
│   ├── hooks/                  # Custom React hooks
│   │   ├── usePatients.ts
│   │   ├── useJourneys.ts
│   │   ├── useRealtime.ts      # WebSocket hook
│   │   └── useAIAssistant.ts   # AI assistant hook
│   ├── utils/                  # Utility functions
│   │   ├── date.ts
│   │   ├── formatting.ts
│   │   └── validation.ts
│   └── types/                  # TypeScript types
│       ├── patient.ts
│       ├── journey.ts
│       └── api.ts
├── public/                     # Static assets
└── styles/                     # Global styles
```

---

## 🎨 Key Features & UI Components

### 1. Dashboard Home
**Purpose:** Overview of key metrics and recent activity

**Components:**
- **Metric Cards**
  - Active journey instances
  - Appointments today/this week
  - Pending tickets
  - Communications sent today
- **Recent Activity Feed**
  - Latest patient registrations
  - Journey stage completions
  - Appointment bookings
  - Ticket updates
- **Quick Actions**
  - Create patient
  - Book appointment
  - Send communication
  - Create ticket

**Widgets:**
- **Journey Status Chart** (pie/donut chart)
- **Appointment Timeline** (calendar view)
- **Communication Analytics** (bar chart by channel)

---

### 2. Patient 360° View
**Purpose:** Comprehensive view of individual patient

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Patient Header (Name, MRN, Photo, Quick Actions)   │
├──────────────┬──────────────────────────────────────┤
│   Sidebar    │   Main Content Area                  │
│   - Overview │   ┌──────────────────────────────┐  │
│   - Journeys │   │  Tab Content                 │  │
│   - Appts    │   │  (Dynamic based on selection)│  │
│   - Comms    │   │                              │  │
│   - Tickets  │   │                              │  │
│   - Documents│   │                              │  │
│   - Timeline │   └──────────────────────────────┘  │
└──────────────┴──────────────────────────────────────┘
```

**Tabs:**
1. **Overview**
   - Demographics
   - Contact information
   - Identifiers (MRN, ABHA, etc.)
   - Medical summary
   - Active consents

2. **Journeys**
   - Active journey instances with progress bars
   - Current stage indicator
   - Stage timeline visualization
   - Journey history

3. **Appointments**
   - Upcoming appointments (card list)
   - Past appointments
   - Appointment calendar
   - Quick book button

4. **Communications**
   - Timeline of all communications
   - Filter by channel (WhatsApp, SMS, Email)
   - Send new message button
   - Message templates dropdown

5. **Tickets**
   - Open tickets
   - Ticket history
   - Create ticket button

6. **Timeline**
   - Unified activity timeline
   - All events chronologically
   - Filterable by type

---

### 3. Journey Management

#### Journey Definitions
**Purpose:** Create and manage journey templates

**Features:**
- **Journey List** (table view)
  - Name, Type, # Stages, # Active Instances
  - Default journey indicator
  - Active/Inactive toggle
- **Journey Builder** (drag-and-drop)
  - Visual stage editor
  - Stage configuration panel
  - Trigger event selector
  - Action configuration (send communication, create task, etc.)
  - Save as template

#### Journey Instances
**Purpose:** Monitor active patient journeys

**Features:**
- **Instance List** (filterable table)
  - Patient name, Journey name, Current stage, Progress %
  - Filters: Journey type, Status, Date range
- **Instance Detail** (Kanban or timeline view)
  - Stage cards with status indicators
  - Patient context panel
  - Manual stage advancement button
  - Stage notes/comments

**Journey Visualization:**
```
Pre-Visit ─✓─> Day of Visit ─●─> Post-Visit ─○─> Follow-up ─○─>
  (Done)       (In Progress)     (Pending)       (Pending)
```

---

### 4. Appointment Management

#### Calendar View
**Purpose:** Visual appointment schedule

**Features:**
- **Month/Week/Day views**
- **Practitioner filtering**
- **Location filtering**
- **Color coding** by appointment type/status
- **Drag-and-drop rescheduling**
- **Click to view/edit appointment details**

#### Appointment List
**Purpose:** Tabular view of appointments

**Features:**
- **Filterable table**
  - Date range, Practitioner, Patient, Status
- **Bulk actions**
  - Send reminders
  - Export to CSV
- **Quick status updates** (Checked-in, Completed, No-show)

#### Slot Management
**Purpose:** Configure provider availability

**Features:**
- **Provider Schedule Builder**
  - Recurring schedule templates (Mon-Fri 9-5)
  - Slot duration configuration
  - Location assignment
  - Capacity per slot
- **Slot Availability View**
  - Real-time slot status (Available, Booked, Blocked)
  - Manual slot blocking for holidays/breaks

---

### 5. Communication Center

#### Communication Timeline
**Purpose:** View all patient communications

**Features:**
- **Unified inbox** (all channels)
- **Channel filters** (WhatsApp, SMS, Email, Voice)
- **Status indicators** (Sent, Delivered, Read, Failed)
- **Conversation threading** (group related messages)
- **Search and filters**
  - By patient, date range, channel, status

#### Send Communication
**Purpose:** Create and send messages

**Features:**
- **Multi-channel composer**
  - Channel selector (WhatsApp, SMS, Email)
  - Template selector (pre-defined templates)
  - Variable substitution ({{patient_name}}, {{appointment_time}})
  - Preview before send
- **Scheduled sending**
  - Schedule for future delivery
  - Recurring messages (reminders)
- **Bulk messaging**
  - Select multiple patients
  - Apply filters (e.g., all patients with appointments tomorrow)

#### Templates
**Purpose:** Manage message templates

**Features:**
- **Template library**
  - Create, edit, delete templates
  - Categorize by type (Reminder, Confirmation, Follow-up)
  - Variable placeholders
  - Multi-language support

---

### 6. Ticket Management

#### Ticket List
**Purpose:** View and manage support tickets

**Features:**
- **Filterable table**
  - Status, Priority, Assigned to, Patient, Date
  - Sort by creation date, priority
- **Quick filters**
  - My tickets, Unassigned, High priority, Overdue
- **Status workflow** (Open → In Progress → Resolved → Closed)

#### Ticket Detail
**Purpose:** View and update ticket

**Features:**
- **Ticket header** (Title, Patient, Priority, Status)
- **Description and comments thread**
- **Assignment** (assign to staff member)
- **Linked resources** (Journey instance, Appointment)
- **Activity log** (who did what when)
- **Resolution notes**

---

### 7. AI Assistant Integration 🤖

**Purpose:** Natural language interface for PRM operations

#### Text Chat Interface
**Reuse from Chitchat:**
- Chat window (sliding panel or modal)
- Message history
- Typing indicators
- Streaming LLM responses
- Markdown rendering

#### Voice Input
**Features:**
- **Voice activation button** (microphone icon)
- **Real-time transcription display**
- **Voice command examples**:
  - "Show me all patients with appointments tomorrow"
  - "Book an appointment for patient with phone number 9844111173 with Dr. Rajiv Sharma for cardiology at 10 AM tomorrow"
  - "Send a WhatsApp reminder to all patients with appointments today"
  - "Create a ticket for patient John Doe about billing issue"

#### Natural Language Command Processing
**Backend LLM Flow:**
1. User provides natural language input (text or voice)
2. Send to backend LLM service
3. LLM extracts structured data:
   ```json
   {
     "intent": "book_appointment",
     "entities": {
       "patient_phone": "9844111173",
       "practitioner_name": "Dr. Rajiv Sharma",
       "speciality": "cardiology",
       "date": "2024-11-19",
       "time": "10:00"
     }
   }
   ```
4. Frontend pre-fills form or executes action
5. Show confirmation UI before finalizing

#### AI Assistant Features
- **Contextual suggestions** based on current page
- **Form auto-fill** from natural language
- **Smart search** (semantic search for patients, appointments)
- **Action confirmation dialogs** (prevent accidental actions)
- **Multi-turn conversations** (clarify ambiguous requests)

**Example Interaction:**
```
User: "Book appointment for 9844111173 with Dr. Rajiv tomorrow at 10AM"
AI: "I found patient Arun Sharma with phone 9844111173. I'll book with Dr. Rajiv Sharma (Cardiology) for Nov 19, 2024 at 10:00 AM. Available slots:
     - 10:00 AM ✓
     - 10:30 AM
     Shall I proceed with 10:00 AM?"
User: "Yes"
AI: "Appointment booked successfully! Confirmation sent via WhatsApp."
```

---

## 📱 Responsive Design

### Mobile-First Approach
- Fully responsive layouts
- Touch-optimized interactions
- Mobile-specific navigation (bottom nav bar)
- Swipe gestures for common actions

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

---

## 🔐 Authentication & Authorization

### Features
- **SSO Integration** (if applicable)
- **Role-Based Access Control (RBAC)**
  - Admin, Doctor, Nurse, Receptionist, Care Coordinator
  - Granular permissions per role
- **Session management**
- **Multi-tenancy support** (hospital/clinic isolation)

---

## 🌊 Real-time Features

### WebSocket Integration
**Events to listen for:**
- New appointment booked
- Journey stage changed
- Communication received/delivered
- Ticket created/updated
- Patient data updated

**UI Updates:**
- Toast notifications for important events
- Badge counters (unread messages, pending tickets)
- Live data refresh without page reload
- Optimistic UI updates

---

## 🎨 Design System

### Color Palette
- **Primary**: Healthcare blue (#0066CC)
- **Success**: Green (#10B981)
- **Warning**: Orange (#F59E0B)
- **Error**: Red (#EF4444)
- **Neutral**: Grays (#F9FAFB to #111827)

### Typography
- **Headings**: Inter or Poppins
- **Body**: Inter or System UI
- **Mono**: JetBrains Mono (for code/IDs)

### Component Standards
- Use Shadcn/ui components consistently
- Follow WAI-ARIA accessibility guidelines
- Keyboard navigation support
- Screen reader compatibility

---

## 🚀 Performance Optimization

### Strategies
1. **Code Splitting**
   - Route-based splitting
   - Component lazy loading
   - Dynamic imports for heavy components

2. **Caching**
   - React Query for server state caching
   - SWR for real-time data
   - Service Worker for offline capability

3. **Image Optimization**
   - Next.js Image component
   - WebP format with fallbacks
   - Lazy loading below fold

4. **Bundle Size**
   - Tree shaking
   - Minimize third-party libraries
   - Analyze bundle with webpack-bundle-analyzer

5. **API Optimization**
   - Pagination for large lists
   - Virtual scrolling for long tables
   - Debounced search inputs
   - Request deduplication

---

## 🧪 Testing Strategy

### Unit Tests
- **Vitest** or **Jest** for component testing
- **React Testing Library** for interaction testing
- Coverage target: 80%+

### Integration Tests
- **Playwright** or **Cypress** for E2E testing
- Critical user flows:
  - Login and authentication
  - Patient creation
  - Appointment booking flow
  - Journey instance creation
  - AI assistant command execution

### Accessibility Testing
- **axe-core** for automated a11y testing
- Manual keyboard navigation testing
- Screen reader compatibility

---

## 📦 Deployment

### CI/CD Pipeline
1. **Build**
   - Run linter (ESLint)
   - Run type checker (TypeScript)
   - Run tests
   - Build production bundle

2. **Deploy**
   - **Staging**: Auto-deploy from `develop` branch
   - **Production**: Manual approval from `main` branch
   - Platform: **Vercel** or **AWS Amplify** or **Docker + Kubernetes**

### Environment Variables
```bash
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_WS_URL=wss://api.yourapp.com/ws
NEXT_PUBLIC_TENANT_ID=default
```

---

## 📊 Analytics & Monitoring

### Tools
- **Vercel Analytics** - Performance metrics
- **Sentry** - Error tracking
- **PostHog** or **Mixpanel** - User behavior analytics
- **LogRocket** - Session replay (optional)

### Key Metrics
- **Performance**
  - Time to First Byte (TTFB)
  - Largest Contentful Paint (LCP)
  - Cumulative Layout Shift (CLS)
  - First Input Delay (FID)

- **User Engagement**
  - Daily/Monthly Active Users
  - Feature adoption rates
  - AI assistant usage metrics
  - Average session duration

---

## 🗓️ Implementation Timeline

### Phase 1: Foundation (Weeks 1-3)
- [ ] Project setup (Next.js, TypeScript, Tailwind)
- [ ] Design system & component library
- [ ] Authentication & layout
- [ ] API client setup with React Query
- [ ] Basic routing structure

### Phase 2: Core Features (Weeks 4-8)
- [ ] Dashboard home
- [ ] Patient 360° view
- [ ] Patient list & creation
- [ ] Basic journey instance view
- [ ] Appointment calendar
- [ ] Communication timeline

### Phase 3: Advanced Features (Weeks 9-12)
- [ ] Journey builder (drag-and-drop)
- [ ] Ticket management
- [ ] Slot management
- [ ] Communication templates
- [ ] Bulk operations

### Phase 4: AI Integration (Weeks 13-16)
- [ ] Integrate chitchat components
- [ ] Text chat interface
- [ ] Voice input capability
- [ ] Natural language command parsing
- [ ] Form auto-fill from AI

### Phase 5: Polish & Testing (Weeks 17-20)
- [ ] E2E testing
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Mobile responsiveness testing
- [ ] User acceptance testing (UAT)

### Phase 6: Deployment (Week 21)
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] User training
- [ ] Documentation

---

## 🔗 Integration with Backend

### API Endpoints
```typescript
// Patient API
GET    /api/v1/patients
POST   /api/v1/patients
GET    /api/v1/patients/{id}
PATCH  /api/v1/patients/{id}

// Journey API
GET    /api/v1/prm/journeys
POST   /api/v1/prm/journeys
GET    /api/v1/prm/instances
POST   /api/v1/prm/instances
POST   /api/v1/prm/instances/{id}/advance

// Appointment API
GET    /api/v1/appointments
POST   /api/v1/appointments
GET    /api/v1/appointments/{id}
PATCH  /api/v1/appointments/{id}

// Communication API
GET    /api/v1/prm/communications
POST   /api/v1/prm/communications

// Ticket API
GET    /api/v1/prm/tickets
POST   /api/v1/prm/tickets
PATCH  /api/v1/prm/tickets/{id}

// AI Assistant API
POST   /api/v1/prm/ai-assistant/parse-command
POST   /api/v1/prm/ai-assistant/chat
```

### WebSocket Events
```typescript
// Subscribe to events
socket.on('appointment:created', (data) => { ... })
socket.on('journey:stage_changed', (data) => { ... })
socket.on('communication:received', (data) => { ... })
socket.on('ticket:updated', (data) => { ... })
```

---

## 📚 Documentation

### Developer Documentation
- **Setup Guide** - Local development setup
- **Component Library** - Storybook for UI components
- **API Documentation** - Auto-generated from OpenAPI spec
- **Architecture Diagrams** - System architecture, data flow

### User Documentation
- **User Manual** - Feature guide for end users
- **Video Tutorials** - Screen recordings for key workflows
- **FAQ** - Common questions and troubleshooting

---

## 🎯 Success Criteria

### User Experience
- ✅ Intuitive navigation (< 3 clicks to any feature)
- ✅ Fast page loads (< 1s for most pages)
- ✅ Mobile-friendly (works on tablets and phones)
- ✅ Accessible (WCAG 2.1 Level AA compliance)

### Functionality
- ✅ All core features implemented
- ✅ AI assistant accurately executes 90%+ of commands
- ✅ Real-time updates work reliably
- ✅ Zero critical bugs in production

### Performance
- ✅ Lighthouse score > 90 for all categories
- ✅ API response rendering < 200ms
- ✅ Bundle size < 500KB (gzipped)

---

## 🚧 Future Enhancements (Post-MVP)

1. **Advanced Analytics Dashboard**
   - Journey completion rates
   - Appointment no-show analysis
   - Communication response rates
   - Patient satisfaction metrics

2. **Mobile Apps** (iOS & Android)
   - React Native or Flutter
   - Native push notifications
   - Offline mode

3. **Patient Portal**
   - Self-service appointment booking
   - View journey progress
   - Secure messaging with care team

4. **Advanced AI Features**
   - Predictive analytics (risk of no-show, readmission)
   - Automated journey optimization
   - Intelligent appointment scheduling

5. **Integrations**
   - EHR systems (Epic, Cerner)
   - Payment gateways
   - Lab systems
   - Pharmacy systems

---

## 📞 Support & Maintenance

### Ongoing Support
- **Bug Fixes**: 24-48 hour SLA for critical issues
- **Feature Requests**: Quarterly release cycle
- **Updates**: Monthly security patches
- **Training**: Onboarding for new users

---

**Prepared by:** Claude (Healthcare Systems Expert)
**Last Updated:** November 18, 2024
**Status:** Ready for Review and Approval