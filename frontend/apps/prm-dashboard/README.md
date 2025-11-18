# PRM Dashboard - Agent-Native Healthcare Interface

**Revolutionary AI-first patient relationship management dashboard**

## 🎯 Vision

This is not a traditional healthcare software with "AI features." This is an **agent-native system** where AI is the primary interface for all operations. Healthcare staff can work at the speed of thought using natural language (text or voice).

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- pnpm 8+
- OpenAI API key
- PRM Backend running (default: http://localhost:8000)

### Installation

```bash
# Install dependencies
cd /Users/paruljuniwal/kuzushi_labs/healthcare/healthtech-redefined/frontend/apps/prm-dashboard
pnpm install

# Copy environment variables
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Run development server
pnpm dev

# Open http://localhost:3000
```

### Build for Production

```bash
pnpm build
pnpm start
```

## 📁 Project Structure

```
prm-dashboard/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication routes
│   │   └── login/
│   ├── (dashboard)/              # Main dashboard routes
│   │   ├── layout.tsx            # Dashboard layout
│   │   ├── page.tsx              # Dashboard home
│   │   ├── patients/             # Patient management
│   │   ├── appointments/         # Appointment calendar
│   │   ├── journeys/             # Journey management
│   │   ├── communications/       # Communication center
│   │   ├── tickets/              # Support tickets
│   │   └── settings/             # System settings
│   ├── globals.css               # Global styles
│   └── layout.tsx                # Root layout
│
├── components/                   # React components
│   ├── ui/                       # Core UI components (Shadcn/ui)
│   ├── ai-assistant/             # AI assistant components
│   │   ├── AIPanel.tsx           # Main AI panel
│   │   ├── ChatInterface.tsx    # Text chat
│   │   ├── VoiceControl.tsx     # Voice input
│   │   ├── CommandBar.tsx       # Cmd+K interface
│   │   └── ConfirmationCard.tsx # Action confirmation
│   ├── patients/                 # Patient components
│   ├── appointments/             # Appointment components
│   ├── journeys/                 # Journey components
│   ├── communications/           # Communication components
│   ├── common/                   # Common components
│   └── layout/                   # Layout components
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
│   │   │   ├── types.ts         # Tool interfaces
│   │   │   ├── registry.ts      # Tool registry
│   │   │   ├── appointment-tools.ts
│   │   │   ├── patient-tools.ts
│   │   │   ├── journey-tools.ts
│   │   │   └── communication-tools.ts
│   │   ├── intent-parser.ts     # LLM intent parsing
│   │   ├── agent-router.ts      # Routes intent to agent
│   │   └── orchestrator.ts      # Main orchestration
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
│   │   └── useAgents.ts         # Agent orchestration
│   ├── utils/                    # Utility functions
│   │   ├── cn.ts                 # Class name merging
│   │   ├── date.ts               # Date formatting
│   │   └── formatting.ts         # Data formatting
│   ├── types/                    # TypeScript types
│   │   └── index.ts              # All type definitions
│   └── store/                    # Zustand stores
│       ├── ui-store.ts           # UI state
│       ├── user-store.ts         # User preferences
│       └── assistant-store.ts    # AI assistant state
│
├── public/                       # Static assets
│   ├── icons/
│   └── images/
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .env.local.example
```

## 🤖 Agent-Native Architecture

### Core Concept

Instead of navigating menus and filling forms, you talk to specialized AI agents:

```typescript
// Traditional way (15+ clicks)
User clicks "Appointments" → "New" → Fills 10+ fields → "Save" → "Send confirmation"

// Agent-native way (1 command)
User: "Schedule callback for patient arunank tomorrow at 2pm"
AI: ✅ Done! Callback scheduled. Reminder sent.
```

### Specialized Agents

| Agent | Handles | Example Commands |
|-------|---------|------------------|
| **AppointmentAgent** | Booking, rescheduling, cancellation | "Schedule appointment..." |
| **JourneyAgent** | Care journey orchestration | "Start onboarding journey..." |
| **CommunicationAgent** | WhatsApp, SMS, Email | "Send reminder to all patients..." |
| **BillingAgent** | Billing, invoicing, payments | "Complete billing for..." |
| **PatientAgent** | Search, CRUD, 360° view | "Find patient with phone..." |
| **TicketAgent** | Support ticket management | "Create ticket for..." |

### Tool System

Agents use atomic tools to execute operations:

```typescript
// Example: AppointmentAgent uses multiple tools
User: "Schedule appointment of arunank with dr. rajiv tomorrow 10am"

AppointmentAgent orchestrates:
  1. patient.search("arunank") → Found Arun Kumar
  2. practitioner.search("dr. rajiv", "orthopaedics")
  3. appointment.check_availability(tomorrow, 10am)
  4. appointment.book(patient, practitioner, slot)
  5. communication.send_whatsapp(patient, confirmation_template)

AI: ✅ Appointment booked! Confirmation sent.
```

## 🎨 Key Features

### 1. AI Assistant Panel (Always Visible)
- **Text & Voice Input** - Switch seamlessly
- **Contextual Suggestions** - Based on current page
- **Recent Actions Log** - See what was done
- **Quick Actions** - One-click common tasks

### 2. Command Bar (Cmd+K)
- **Universal Search** - Find anything
- **Natural Language Commands** - No menu navigation
- **Recent Commands** - Quick access

### 3. Voice Interface
```
[User presses microphone]
User: "Complete billing for patient nine eight four four..."
AI: 🎤 Found Arun Kumar. Amount ₹1,500. Payment method?
User: "Cash"
AI: ✅ Billing completed! Receipt sent.
```

### 4. Confirmation UI
Before executing actions, beautiful confirmation cards:

```
┌──────────────────────────────────────────┐
│ Appointment Booking                      │
├──────────────────────────────────────────┤
│ Patient: Arun Kumar (9844111173)         │
│ Practitioner: Dr. Rajiv Sharma           │
│ Date & Time: Nov 20, 2024 at 10:00 AM    │
│ Confidence: 95% ✓                        │
│                                          │
│ [Confirm & Book] [Modify] [Cancel]       │
└──────────────────────────────────────────┘
```

## 🛠️ Technology Stack

**Frontend:**
- Next.js 14 with App Router
- TypeScript for type safety
- React 18 with Server Components
- Shadcn/ui component library
- Tailwind CSS for styling
- Framer Motion for animations

**State Management:**
- React Query (TanStack Query) - Server state
- Zustand - Client state
- WebSocket - Real-time updates

**AI Integration:**
- OpenAI GPT-4 Turbo - Intent parsing & agents
- LangChain - Agent framework
- Healthcare Conversation Platform - Voice & text

**Data Visualization:**
- Recharts - Charts and graphs
- React Flow - Journey visualization

## ✅ Implementation Status

**Fully Implemented Features:**

### Pages (9/9 Complete)
- ✅ Landing Page - Marketing site
- ✅ Dashboard - Analytics with real-time metrics
- ✅ Patients List - Search, filter, and manage patients
- ✅ Patient 360° View - Complete patient profile
- ✅ Appointments Calendar - Day/Week/Month/List views
- ✅ Journeys Management - Progress tracking and visualization
- ✅ Communications Center - Multi-channel messaging (WhatsApp/SMS/Email)
- ✅ Tickets Management - Support ticket tracking
- ✅ Settings - User, organization, and AI configuration

### AI System (30/30 Tools, 5/5 Agents)
- ✅ **AppointmentAgent** - 5 tools (book, reschedule, cancel, get slots, get)
- ✅ **PatientAgent** - 5 tools (search, get, create, update, get 360)
- ✅ **JourneyAgent** - 7 tools (create, get, add step, complete step, complete, list, update)
- ✅ **CommunicationAgent** - 6 tools (WhatsApp, SMS, Email, bulk, templates, history)
- ✅ **TicketAgent** - 7 tools (create, get, update, assign, resolve, close, add comment)

### Infrastructure
- ✅ Orchestrator - Multi-agent coordination
- ✅ Intent Parser - GPT-4 powered classification
- ✅ Tool Registry - Central tool management
- ✅ Agent Registry - Agent discovery and routing
- ✅ Confirmation Workflow - Risk-based approvals
- ✅ API Clients - 6 fully implemented (patients, appointments, journeys, communications, tickets, client)

### UI Components (14/14)
- ✅ Button, Input, Label, Card, Dialog
- ✅ Badge, Avatar, Table
- ✅ AIChat (always-on chat panel)
- ✅ CommandBar (Cmd+K interface)
- ✅ ConfirmationCard (action approval)

## 📊 Statistics

- **Lines of Code**: 10,000+
- **React Components**: 50+
- **API Endpoints**: 30+
- **AI Tools**: 30
- **AI Agents**: 5
- **Pages**: 9
- **UI Components**: 14

## 📚 Documentation

### For Developers
- [Architecture Document](../../docs/PHASE_6_FRONTEND_ARCHITECTURE.md) - Complete system design
- [Agent Implementation Guide](../../docs/PHASE_6_AGENT_IMPLEMENTATION_GUIDE.md) - How to build agents
- [API Integration Guide](../../docs/PRM_FRONTEND_ROADMAP.md) - Backend integration
- [Final Implementation Summary](./FINAL_IMPLEMENTATION_SUMMARY.md) - Complete feature breakdown

### AI System Examples
- [AI Examples](./lib/ai/examples.ts) - 10 real-world usage examples
- [AI README](./lib/ai/README.md) - Complete AI system documentation

### For Users
- User Manual - Feature guide (coming soon)
- Video Tutorials - Recorded demos (coming soon)
- FAQ - Common questions (coming soon)

## 🧪 Testing

```bash
# Run unit tests
pnpm test

# Run E2E tests
pnpm test:e2e

# Type checking
pnpm type-check

# Linting
pnpm lint
```

## 🚀 Deployment

### Environment Variables

Create a `.env.local` file in the project root:

```bash
# Backend API (Required)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# OpenAI API (Required for AI features)
NEXT_PUBLIC_OPENAI_API_KEY=sk-your-openai-api-key-here

# Feature Flags (Optional)
NEXT_PUBLIC_ENABLE_AI=true
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_VOICE=false

# Optional (for voice features)
NEXT_PUBLIC_LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# Environment
NODE_ENV=production
```

### Deployment Options

#### Option 1: Vercel (Recommended for Production)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy PRM Dashboard"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Set root directory to `frontend/apps/prm-dashboard`

3. **Configure Environment Variables**
   Add all variables from `.env.local` in Vercel's dashboard:
   - Go to Settings → Environment Variables
   - Add each variable one by one
   - Make sure to select appropriate environments (Production, Preview, Development)

4. **Deploy**
   - Click "Deploy"
   - Vercel will automatically build and deploy your app
   - You'll get a production URL like `https://your-app.vercel.app`

5. **Custom Domain (Optional)**
   - Go to Settings → Domains
   - Add your custom domain
   - Update DNS records as instructed

**Vercel Advantages:**
- Automatic HTTPS
- Global CDN
- Zero-config deployment
- Automatic previews for PRs
- Edge functions support
- Built-in analytics

#### Option 2: Docker Deployment

1. **Create Dockerfile** (if not exists):

```dockerfile
# Multi-stage build for optimal image size
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED 1

# Build application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

2. **Build Docker Image**:
   ```bash
   docker build -t prm-dashboard:latest .
   ```

3. **Run Container**:
   ```bash
   docker run -d \
     --name prm-dashboard \
     -p 3000:3000 \
     -e NEXT_PUBLIC_API_BASE_URL=https://your-api.com \
     -e NEXT_PUBLIC_OPENAI_API_KEY=sk-... \
     prm-dashboard:latest
   ```

4. **Docker Compose** (for complete stack):

```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
      - NEXT_PUBLIC_OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - backend
    networks:
      - prm-network

  backend:
    image: prm-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/prm
    networks:
      - prm-network

networks:
  prm-network:
    driver: bridge
```

Run with: `docker-compose up -d`

#### Option 3: Self-Hosted (VM/VPS)

1. **Server Requirements**:
   - Ubuntu 22.04 LTS or similar
   - Node.js 18+
   - Nginx (for reverse proxy)
   - 2GB RAM minimum
   - 20GB disk space

2. **Install Dependencies**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Node.js
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs

   # Install npm/pnpm
   npm install -g pnpm

   # Install PM2 (process manager)
   npm install -g pm2
   ```

3. **Clone and Build**:
   ```bash
   git clone https://github.com/your-org/healthtech-redefined.git
   cd healthtech-redefined/frontend/apps/prm-dashboard
   pnpm install
   pnpm build
   ```

4. **Start with PM2**:
   ```bash
   pm2 start npm --name "prm-dashboard" -- start
   pm2 save
   pm2 startup  # Enable auto-start on reboot
   ```

5. **Configure Nginx**:

   Create `/etc/nginx/sites-available/prm-dashboard`:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/prm-dashboard /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **SSL with Let's Encrypt**:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

#### Option 4: AWS EC2 + Load Balancer

1. **Launch EC2 Instance**:
   - AMI: Ubuntu 22.04
   - Instance Type: t3.medium (2 vCPU, 4GB RAM)
   - Security Group: Allow HTTP (80), HTTPS (443), SSH (22)

2. **Setup Application** (same as self-hosted steps above)

3. **Configure Load Balancer**:
   - Create Application Load Balancer
   - Target Group: Point to EC2 instance on port 3000
   - Health Check: /api/health
   - SSL Certificate: ACM or upload custom

4. **Auto Scaling** (optional):
   - Create Launch Template from EC2 instance
   - Create Auto Scaling Group
   - Min: 2, Max: 10 instances
   - Scaling Policy: CPU > 70%

### Post-Deployment Checklist

- [ ] Environment variables set correctly
- [ ] OpenAI API key configured
- [ ] Backend API accessible
- [ ] SSL certificate installed (production)
- [ ] DNS records configured
- [ ] Health checks passing
- [ ] Error tracking setup (Sentry/etc)
- [ ] Analytics configured
- [ ] Backup strategy in place
- [ ] Monitoring setup (uptime, performance)
- [ ] User acceptance testing completed

### Monitoring & Maintenance

**Recommended Tools:**
- **Uptime**: UptimeRobot, Pingdom
- **Error Tracking**: Sentry, LogRocket
- **Analytics**: Vercel Analytics, Google Analytics
- **Performance**: Lighthouse CI, Web Vitals
- **Logs**: Papertrail, Logtail

**Regular Maintenance:**
```bash
# Update dependencies monthly
pnpm update

# Security audit
pnpm audit
pnpm audit fix

# Check for outdated packages
pnpm outdated
```

## 🎯 Success Metrics

**UX Goals:**
- 90% of users can complete tasks without training
- < 1s page load time
- < 200ms interaction response time
- WCAG 2.1 AA accessibility

**AI Goals:**
- 95%+ intent recognition accuracy
- 90%+ successful action execution
- < 2s AI response time

## 🔐 Security & Compliance

- JWT-based authentication
- Role-based access control (RBAC)
- HIPAA-compliant PHI handling
- Encrypted data at rest and in transit
- Audit logging for all operations

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development guidelines.

## 📄 License

Proprietary - All rights reserved

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourorg/healthtech-redefined/issues)
- Email: support@yourcompany.com
- Documentation: [Docs Site](https://docs.yourcompany.com)

---

**Built with ❤️ by the Healthcare Innovation Team**

**Powered by Claude AI**

🎉 **Welcome to the future of healthcare software!** 🎉
