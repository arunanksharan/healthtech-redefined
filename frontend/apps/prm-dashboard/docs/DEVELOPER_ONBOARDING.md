# PRM Dashboard - Developer Onboarding Guide

Welcome to the PRM Dashboard development team! This guide will help you get started quickly and productively.

## Table of Contents

1. [Welcome](#welcome)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Project Structure](#project-structure)
5. [Key Technologies](#key-technologies)
6. [Architecture Overview](#architecture-overview)
7. [Development Workflow](#development-workflow)
8. [Code Standards](#code-standards)
9. [Testing](#testing)
10. [Security](#security)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)
13. [Resources](#resources)

## Welcome

The PRM Dashboard is a comprehensive Patient Relationship Management system for healthcare providers. As a developer on this project, you'll be working with cutting-edge technologies to build features that directly impact patient care.

**What We're Building:**
- Patient management system
- Appointment scheduling
- Care journey tracking
- Multi-channel communications
- AI-powered assistant
- HIPAA-compliant healthcare platform

**Tech Stack:**
- Next.js 15.0.3 with App Router
- React 19.0.0
- TypeScript 5.6.3
- Tailwind CSS 3.4.1
- Zod for validation
- Jest + Playwright for testing

## Prerequisites

Before you begin, ensure you have:

**Required:**
- Node.js 18+ (LTS recommended)
- npm 9+ or yarn 1.22+
- Git 2.30+
- Code editor (VS Code recommended)
- Basic understanding of React and TypeScript

**Recommended:**
- Docker (for backend services)
- Postman or similar (for API testing)
- React DevTools browser extension
- PostgreSQL (for local database)

**Knowledge:**
- JavaScript/TypeScript
- React fundamentals
- RESTful APIs
- Git workflow
- Basic healthcare domain knowledge (helpful but not required)

## Environment Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/healthtech/prm-dashboard.git
cd prm-dashboard/frontend/apps/prm-dashboard

# Or if you have access via SSH
git clone git@github.com:healthtech/prm-dashboard.git
cd prm-dashboard/frontend/apps/prm-dashboard
```

### 2. Install Dependencies

```bash
# Install dependencies
npm install

# Or with yarn
yarn install
```

### 3. Environment Variables

Create a `.env.local` file in the root directory:

```bash
# Copy the example file
cp .env.example .env.local
```

**Required environment variables:**

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Authentication
NEXT_PUBLIC_AUTH_DOMAIN=your-auth-domain.com
JWT_SECRET=your_jwt_secret_here

# Feature Flags
NEXT_PUBLIC_ENABLE_AI=true
NEXT_PUBLIC_ENABLE_WHATSAPP=true
NEXT_PUBLIC_ENABLE_SMS=true

# Monitoring (Optional)
NEXT_PUBLIC_SENTRY_DSN=
NEXT_PUBLIC_ANALYTICS_ID=

# Development
NODE_ENV=development
```

**Getting API Keys:**
- OpenAI API key: https://platform.openai.com/api-keys
- Sentry DSN (optional): https://sentry.io

### 4. Start Development Server

```bash
# Start the development server
npm run dev

# Or with yarn
yarn dev
```

The application will be available at http://localhost:3000

### 5. Verify Setup

Visit http://localhost:3000 and you should see the login page. If you see errors, check:
- All dependencies installed correctly
- Environment variables set properly
- Backend services running (if applicable)
- No port conflicts (3000 is available)

## Project Structure

```
prm-dashboard/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth-related pages
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/              # Main dashboard pages
│   │   ├── patients/
│   │   ├── appointments/
│   │   ├── journeys/
│   │   ├── communications/
│   │   ├── tickets/
│   │   └── settings/
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page
│   └── globals.css               # Global styles
│
├── components/                   # Reusable components
│   ├── ui/                       # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── ai-chat-panel.tsx         # AI assistant UI
│   ├── error-boundary.tsx        # Error handling
│   └── ...
│
├── lib/                          # Utilities and core logic
│   ├── ai/                       # AI agent system
│   │   ├── agents/               # Individual agents
│   │   ├── tools/                # AI tools
│   │   ├── orchestrator.ts       # Agent coordination
│   │   └── openai.ts             # OpenAI integration
│   ├── api/                      # API clients
│   │   ├── patients.ts
│   │   ├── appointments.ts
│   │   └── ...
│   ├── auth/                     # Authentication
│   │   ├── auth.ts               # Auth utilities
│   │   └── guards.tsx            # Route guards
│   ├── security/                 # Security utilities
│   │   ├── audit-log.ts          # Audit logging
│   │   ├── encryption.ts         # Encryption
│   │   ├── rate-limiter.ts       # Rate limiting
│   │   └── session.ts            # Session management
│   ├── validation/               # Form validation
│   │   └── schemas.ts            # Zod schemas
│   └── utils.ts                  # Helper functions
│
├── hooks/                        # Custom React hooks
│   ├── use-auth.ts
│   ├── use-patients.ts
│   └── ...
│
├── types/                        # TypeScript types
│   ├── patient.ts
│   ├── appointment.ts
│   └── ...
│
├── docs/                         # Documentation
│   ├── USER_GUIDE.md
│   ├── ADMINISTRATOR_GUIDE.md
│   ├── API_DOCUMENTATION.md
│   └── DEVELOPER_ONBOARDING.md   # This file
│
├── e2e/                          # End-to-end tests
│   ├── appointments.spec.ts
│   └── ...
│
├── public/                       # Static assets
│   ├── images/
│   └── fonts/
│
├── scripts/                      # Utility scripts
│   └── security-scan.sh
│
├── .env.example                  # Environment template
├── .env.local                    # Your local env (git-ignored)
├── next.config.js                # Next.js configuration
├── tailwind.config.ts            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
├── jest.config.js                # Jest configuration
├── playwright.config.ts          # Playwright configuration
└── package.json                  # Dependencies
```

### Key Directories

**`app/`** - Next.js 13+ App Router
- Route groups: `(auth)` and `(dashboard)` for different layouts
- Each folder represents a route
- `layout.tsx` defines shared UI
- `page.tsx` is the actual page component

**`components/`** - Reusable UI components
- `ui/` contains shadcn/ui components
- Organized by feature or function
- Should be pure and well-tested

**`lib/`** - Core business logic and utilities
- `ai/` - AI agent system (orchestrator, agents, tools)
- `api/` - API client functions
- `auth/` - Authentication and authorization
- `security/` - Security utilities (encryption, audit, etc.)
- `validation/` - Zod schemas for forms

**`hooks/`** - Custom React hooks
- Encapsulate reusable stateful logic
- Follow `use*` naming convention

## Key Technologies

### Next.js 15.0.3

**App Router:**
- File-system based routing
- Server and Client Components
- Layouts and nested routes
- Route groups for different layouts

**Key Concepts:**
```typescript
// Server Component (default)
export default async function Page() {
  const data = await fetchData(); // Can fetch directly
  return <div>{data}</div>;
}

// Client Component (when you need interactivity)
'use client';

export default function ClientPage() {
  const [state, setState] = useState();
  return <div>{state}</div>;
}
```

**Learn More:** https://nextjs.org/docs

### React 19.0.0

**Modern Features We Use:**
- Hooks (useState, useEffect, useCallback, useMemo)
- Context API for state management
- Error boundaries for error handling
- Suspense for loading states

### TypeScript 5.6.3

**Why TypeScript:**
- Type safety prevents bugs
- Better IDE support (autocomplete, refactoring)
- Self-documenting code
- Easier refactoring

**Key Patterns:**
```typescript
// Interface for data structures
interface Patient {
  id: string;
  name: string;
  email: string;
  date_of_birth: string;
}

// Type for function props
type PatientCardProps = {
  patient: Patient;
  onEdit: (id: string) => void;
};

// Generics for reusable types
type ApiResponse<T> = {
  success: boolean;
  data: T;
};
```

### Tailwind CSS 3.4.1

**Utility-First CSS:**
```tsx
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm">
  <h2 className="text-lg font-semibold">Title</h2>
  <Button className="px-4 py-2">Action</Button>
</div>
```

**Custom Configuration:**
- Custom colors in `tailwind.config.ts`
- Custom utilities and components
- Dark mode support

### Zod

**Type-Safe Validation:**
```typescript
import { z } from 'zod';

const patientSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/),
});

type Patient = z.infer<typeof patientSchema>;

// Use in forms
const result = patientSchema.safeParse(formData);
if (!result.success) {
  console.error(result.error.errors);
}
```

### shadcn/ui

**Component Library:**
- Not a package, components are copied to your project
- Fully customizable
- Built with Radix UI primitives
- Styled with Tailwind CSS

**Adding Components:**
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add dialog
```

## Architecture Overview

### AI Agent System

The core innovation of the PRM Dashboard is the AI-powered assistant.

**Architecture:**
```
User Input → Orchestrator → Agent Selection → Tool Execution → Response
```

**Components:**

1. **Orchestrator** (`lib/ai/orchestrator.ts`)
   - Routes requests to appropriate agents
   - Manages conversation context
   - Handles multi-step operations

2. **Agents** (`lib/ai/agents/`)
   - Specialized for specific domains
   - PatientAgent: Patient operations
   - AppointmentAgent: Scheduling
   - JourneyAgent: Care journeys
   - CommunicationAgent: Messaging
   - TicketAgent: Support tickets

3. **Tools** (`lib/ai/tools/`)
   - Actual functions agents can call
   - Interact with API
   - Return structured data

**Example Agent:**
```typescript
export class PatientAgent implements Agent {
  name = 'patient_agent';
  capabilities = ['patient management', 'patient search'];

  canHandle(input: string): boolean {
    const keywords = ['patient', 'create patient', 'find patient'];
    return keywords.some(k => input.toLowerCase().includes(k));
  }

  async process(input: string, context: ConversationContext) {
    const intent = this.parseIntent(input);

    if (intent === 'create') {
      return this.createPatient(input, context);
    } else if (intent === 'search') {
      return this.searchPatients(input, context);
    }
  }
}
```

### Authentication Flow

```
1. User enters credentials
2. Frontend sends to /auth/login
3. Backend validates and returns JWT
4. Frontend stores token in localStorage
5. Token included in all subsequent requests
6. Token validated on backend for each request
7. Refresh token used to get new access token when expired
```

**Implementation:**
- JWT tokens for stateless auth
- Role-based access control (RBAC)
- Permission-based access control
- Route guards protect pages
- Component guards protect UI elements

### State Management

**Current Approach:**
- React Context for global state (auth, theme)
- Local state with useState for component state
- Server state managed by Next.js (Server Components)

**Example Context:**
```typescript
'use client';

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email, password) => {
    const response = await loginAPI(email, password);
    storeTokens(response);
    setUser(response.user);
  };

  return (
    <AuthContext.Provider value={{ user, login }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Security Architecture

**Layered Security:**

1. **Network Layer:**
   - HTTPS/TLS 1.3
   - Security headers (HSTS, X-Frame-Options, etc.)

2. **Application Layer:**
   - JWT authentication
   - RBAC/permissions
   - Session management (30 min timeout)
   - Rate limiting

3. **Data Layer:**
   - AES-256-GCM encryption
   - PII redaction in logs
   - Input validation (Zod)
   - SQL injection prevention

4. **Audit Layer:**
   - Comprehensive logging
   - HIPAA compliance
   - Tamper-evident logs

## Development Workflow

### 1. Pick a Task

Tasks are tracked in:
- GitHub Issues
- Project board
- Sprint planning docs

**Good First Issues:**
Look for issues tagged with `good-first-issue` or `help-wanted`.

### 2. Create a Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Convention:**
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation
- `test/` - Tests

### 3. Development

**Start Development Server:**
```bash
npm run dev
```

**Watch for Changes:**
- Hot reload for code changes
- Error overlay for compile errors
- Console for runtime errors

**Best Practices:**
- Write clean, readable code
- Follow existing patterns
- Add comments for complex logic
- Write tests for new features
- Update documentation

### 4. Testing

**Run Tests:**
```bash
# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run specific test file
npm test -- patients.test.ts

# Run E2E tests
npm run test:e2e

# Run with coverage
npm test -- --coverage
```

**Write Tests:**
```typescript
// Unit test example
import { render, screen } from '@testing-library/react';
import PatientCard from './patient-card';

describe('PatientCard', () => {
  it('renders patient name', () => {
    const patient = { id: '1', name: 'John Doe', ... };
    render(<PatientCard patient={patient} />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

### 5. Code Quality

**Type Checking:**
```bash
npm run type-check
```

**Linting:**
```bash
npm run lint

# Auto-fix
npm run lint -- --fix
```

**Formatting:**
```bash
npm run format
```

**Security Scan:**
```bash
./scripts/security-scan.sh
```

### 6. Commit Changes

**Commit Message Convention:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```bash
git commit -m "feat(patients): add search functionality"
git commit -m "fix(appointments): resolve scheduling conflict bug"
git commit -m "docs(api): update authentication documentation"
```

### 7. Push and Create PR

```bash
# Push branch
git push origin feature/your-feature-name

# Create pull request on GitHub
```

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
```

### 8. Code Review

**As Author:**
- Respond to feedback promptly
- Make requested changes
- Re-request review after updates

**As Reviewer:**
- Be constructive and kind
- Focus on code quality and standards
- Test the changes locally if needed
- Approve when ready

### 9. Merge

Once approved:
- Squash and merge (preferred)
- Merge commit (for complex features)
- Rebase and merge (for clean history)

## Code Standards

### TypeScript

**Use TypeScript everywhere:**
```typescript
// Good
function createPatient(data: PatientInput): Promise<Patient> {
  return api.post('/patients', data);
}

// Bad
function createPatient(data) {
  return api.post('/patients', data);
}
```

**Avoid `any`:**
```typescript
// Good
function processData(data: Patient | Appointment): void {
  // ...
}

// Bad
function processData(data: any): void {
  // ...
}
```

### React Components

**Functional Components:**
```typescript
// Good - Functional component with TypeScript
type Props = {
  patient: Patient;
  onEdit: (id: string) => void;
};

export default function PatientCard({ patient, onEdit }: Props) {
  return (
    <div>
      <h3>{patient.name}</h3>
      <Button onClick={() => onEdit(patient.id)}>Edit</Button>
    </div>
  );
}

// Avoid - Class components (unless necessary)
class PatientCard extends React.Component {
  // ...
}
```

**Component Organization:**
```typescript
// 1. Imports
import { useState } from 'react';
import { Button } from '@/components/ui/button';

// 2. Types
type Props = { ... };

// 3. Component
export default function Component({ prop }: Props) {
  // 4. Hooks
  const [state, setState] = useState();

  // 5. Event handlers
  const handleClick = () => { ... };

  // 6. Effects
  useEffect(() => { ... }, []);

  // 7. Render
  return <div>...</div>;
}
```

### File Naming

- Components: `kebab-case.tsx` (e.g., `patient-card.tsx`)
- Utilities: `kebab-case.ts` (e.g., `date-utils.ts`)
- Types: `kebab-case.ts` (e.g., `patient.ts`)
- Tests: `*.test.ts` or `*.spec.ts`

### Styling

**Use Tailwind Classes:**
```tsx
// Good
<div className="flex items-center gap-4 p-4 bg-white rounded-lg">

// Avoid inline styles
<div style={{ display: 'flex', padding: '16px' }}>
```

**Use cn() for Conditional Classes:**
```tsx
import { cn } from '@/lib/utils';

<Button className={cn(
  "px-4 py-2",
  isPrimary && "bg-blue-600 text-white",
  isDisabled && "opacity-50 cursor-not-allowed"
)}>
```

### API Calls

**Use API Client Functions:**
```typescript
// lib/api/patients.ts
export async function getPatients(params?: GetPatientsParams) {
  const response = await api.get('/patients', { params });
  return response.data;
}

// In component
const patients = await getPatients({ page: 1, limit: 20 });
```

**Handle Errors:**
```typescript
try {
  const patient = await createPatient(data);
  toast.success('Patient created successfully');
} catch (error) {
  if (error instanceof ApiError) {
    toast.error(error.message);
  } else {
    toast.error('An unexpected error occurred');
  }
}
```

### Forms

**Use Zod for Validation:**
```typescript
import { z } from 'zod';
import { useForm } from '@/hooks/use-form';

const schema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
});

export default function PatientForm() {
  const { register, handleSubmit, errors } = useForm(schema);

  const onSubmit = (data) => {
    createPatient(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input {...register('name')} error={errors.name} />
      <Input {...register('email')} error={errors.email} />
      <Button type="submit">Create</Button>
    </form>
  );
}
```

### Security

**Never hardcode secrets:**
```typescript
// Bad
const API_KEY = 'abc123';

// Good
const API_KEY = process.env.OPENAI_API_KEY;
```

**Validate all inputs:**
```typescript
// Always validate with Zod schemas
const result = schema.safeParse(userInput);
if (!result.success) {
  throw new ValidationError(result.error);
}
```

**Use auth guards:**
```typescript
// Protect routes
export default function ProtectedPage() {
  return (
    <AuthGuard>
      <PermissionGuard permission="patient.view">
        <PageContent />
      </PermissionGuard>
    </AuthGuard>
  );
}
```

**Log security events:**
```typescript
import { auditPatient } from '@/lib/security/audit-log';

async function viewPatient(patientId: string) {
  await auditPatient.view(patientId);
  return getPatient(patientId);
}
```

## Testing

### Unit Tests

**What to Test:**
- Component rendering
- User interactions
- State changes
- Edge cases
- Error handling

**Example:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import PatientCard from './patient-card';

describe('PatientCard', () => {
  const mockPatient = {
    id: '123',
    name: 'John Doe',
    email: 'john@example.com',
  };

  it('renders patient information', () => {
    render(<PatientCard patient={mockPatient} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<PatientCard patient={mockPatient} onEdit={onEdit} />);

    fireEvent.click(screen.getByText('Edit'));

    expect(onEdit).toHaveBeenCalledWith('123');
  });
});
```

### Integration Tests

**Test Feature Flows:**
```typescript
describe('Patient Management', () => {
  it('creates and displays new patient', async () => {
    render(<PatientsPage />);

    // Open create dialog
    fireEvent.click(screen.getByText('New Patient'));

    // Fill form
    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'Jane Doe' },
    });

    // Submit
    fireEvent.click(screen.getByText('Create'));

    // Verify patient appears
    await screen.findByText('Jane Doe');
  });
});
```

### E2E Tests

**Test Critical User Journeys:**
```typescript
// e2e/appointments.spec.ts
import { test, expect } from '@playwright/test';

test('book appointment flow', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'provider@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('[type="submit"]');

  // Navigate to appointments
  await page.click('text=Appointments');

  // Create appointment
  await page.click('text=New Appointment');
  await page.fill('[name="patient"]', 'John Doe');
  await page.fill('[name="date"]', '2024-11-25');
  await page.fill('[name="time"]', '14:00');
  await page.click('text=Book');

  // Verify
  await expect(page.locator('text=Appointment booked')).toBeVisible();
});
```

### Test Coverage

**Minimum Requirements:**
- Overall: 70%
- Critical paths: 90%
- Security utilities: 100%

**Check Coverage:**
```bash
npm test -- --coverage
```

## Security

### Authentication

**Check Auth Status:**
```typescript
import { isAuthenticated, getCurrentUser } from '@/lib/auth/auth';

if (!isAuthenticated()) {
  router.push('/login');
  return;
}

const user = getCurrentUser();
```

**Protected Routes:**
```typescript
// app/(dashboard)/layout.tsx
export default function DashboardLayout({ children }) {
  return (
    <AuthGuard>
      {children}
    </AuthGuard>
  );
}
```

### Authorization

**Check Permissions:**
```typescript
import { hasPermission, hasRole } from '@/lib/auth/auth';

if (!hasPermission('patient.delete')) {
  throw new Error('Insufficient permissions');
}

if (hasRole(['admin', 'provider'])) {
  // Show advanced features
}
```

**Conditional Rendering:**
```typescript
import { CanAccess } from '@/lib/auth/guards';

<CanAccess permission="patient.delete">
  <Button onClick={deletePatient}>Delete</Button>
</CanAccess>
```

### Data Protection

**Encrypt Sensitive Data:**
```typescript
import { encrypt, decrypt } from '@/lib/security/encryption';

// Before storing
const encrypted = await encrypt(sensitiveData, encryptionKey);
localStorage.setItem('data', encrypted);

// When retrieving
const encrypted = localStorage.getItem('data');
const data = await decrypt(encrypted, encryptionKey);
```

**Mask PII in Logs:**
```typescript
import { maskEmail, maskPhone } from '@/lib/security/encryption';

console.log(`Email: ${maskEmail(patient.email)}`);
// Output: Email: pa*****@example.com
```

**Audit Logging:**
```typescript
import { auditPatient } from '@/lib/security/audit-log';

async function updatePatient(id: string, changes: Partial<Patient>) {
  await auditPatient.update(id, changes);
  return api.patch(`/patients/${id}`, changes);
}
```

### Input Validation

**Always Validate:**
```typescript
import { createPatientSchema } from '@/lib/validation/schemas';

const result = createPatientSchema.safeParse(formData);
if (!result.success) {
  return { errors: result.error.flatten() };
}

// Safe to use
const patient = await createPatient(result.data);
```

### Security Checklist

Before deploying:
- [ ] All secrets in environment variables
- [ ] Authentication on all protected routes
- [ ] Authorization checks on sensitive operations
- [ ] Input validation on all forms
- [ ] Audit logging for PHI access
- [ ] Error messages don't leak sensitive info
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] Dependencies updated
- [ ] Security scan passed

## Deployment

### Build

```bash
# Production build
npm run build

# Test production build locally
npm run start
```

### Environment Variables

**Production:**
```env
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.healthtech.com/api/v1
NEXT_PUBLIC_WS_URL=wss://api.healthtech.com/ws
OPENAI_API_KEY=prod_key_here
# ... other production settings
```

### Deployment Platforms

**Vercel (Recommended):**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

**Docker:**
```dockerfile
# Dockerfile is in the project root
docker build -t prm-dashboard .
docker run -p 3000:3000 prm-dashboard
```

### CI/CD

**GitHub Actions:**
The project includes CI/CD workflows:
- `.github/workflows/test.yml` - Run tests
- `.github/workflows/deploy.yml` - Deploy to production

**Pre-Deployment Checks:**
```bash
# Run all checks
npm run type-check
npm run lint
npm test
./scripts/security-scan.sh
npm run build
```

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>
```

**Module Not Found:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**TypeScript Errors:**
```bash
# Clear TypeScript cache
rm -rf .next
npm run dev
```

**Build Failures:**
```bash
# Clear cache and rebuild
rm -rf .next
npm run build
```

### Debug Mode

**Enable Verbose Logging:**
```env
DEBUG=*
```

**React DevTools:**
- Install browser extension
- Inspect component tree
- View props and state
- Profile performance

**Network Tab:**
- Monitor API calls
- Check request/response
- Verify headers
- Check status codes

### Getting Help

**Internal:**
- Team Slack channel: #prm-dev
- Daily standup meetings
- Office hours: Tuesday/Thursday 2-3pm

**External:**
- Next.js Docs: https://nextjs.org/docs
- React Docs: https://react.dev
- TypeScript Handbook: https://www.typescriptlang.org/docs
- Stack Overflow (tag: prm-dashboard)

## Resources

### Documentation

**Project Docs:**
- [User Guide](./USER_GUIDE.md)
- [Administrator Guide](./ADMINISTRATOR_GUIDE.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Security & Compliance](../SECURITY_AND_COMPLIANCE.md)

**External:**
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Zod](https://zod.dev)

### Learning Resources

**Next.js:**
- [Next.js Learn Course](https://nextjs.org/learn)
- [Next.js Examples](https://github.com/vercel/next.js/tree/canary/examples)

**React:**
- [React Tutorial](https://react.dev/learn)
- [React Patterns](https://reactpatterns.com)

**TypeScript:**
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript)
- [Type Challenges](https://github.com/type-challenges/type-challenges)

**Testing:**
- [Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro)
- [Playwright Docs](https://playwright.dev/docs/intro)

### Code Examples

**Starter Templates:**
- `examples/patient-form.tsx` - Form with validation
- `examples/api-client.ts` - API client pattern
- `examples/protected-page.tsx` - Auth guards
- `examples/ai-agent.ts` - Custom agent

### Development Tools

**VS Code Extensions:**
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- TypeScript Vue Plugin (Volar)
- GitLens
- Error Lens
- Auto Rename Tag

**Browser Extensions:**
- React Developer Tools
- Redux DevTools (if using Redux)
- JSON Formatter
- Lighthouse

### Team

**Technical Leads:**
- Frontend: Jane Smith (@janesmith)
- Backend: John Doe (@johndoe)
- DevOps: Sarah Johnson (@sarahj)

**Product:**
- Product Manager: Mike Wilson (@mikew)
- UX Designer: Emily Chen (@emilyc)

**Support:**
- Engineering Support: dev-support@healthtech.com
- Security Questions: security@healthtech.com

## Next Steps

Now that you're set up:

1. **Explore the Codebase**
   - Read through the main pages
   - Understand the component structure
   - Review the AI agent system

2. **Pick a Good First Issue**
   - Check GitHub Issues
   - Look for `good-first-issue` label
   - Ask in Slack if you need help

3. **Make Your First Contribution**
   - Fix a small bug
   - Add a test
   - Improve documentation
   - Get familiar with the PR process

4. **Join Team Meetings**
   - Daily standup: 9:30 AM
   - Sprint planning: Mondays 2 PM
   - Demo day: End of each sprint

5. **Learn the Domain**
   - Healthcare basics
   - HIPAA compliance
   - Patient care workflows
   - Clinical terminology

## Welcome Aboard!

We're excited to have you on the team. Don't hesitate to ask questions - we're all here to help each other build amazing software that improves patient care.

**Remember:**
- Quality over speed
- Security first
- Patient privacy is paramount
- Test thoroughly
- Document well
- Be kind and collaborative

Happy coding!

---

**Last Updated:** November 19, 2024
**Version:** 1.0
**For:** New Developers

**Questions?** Contact dev-support@healthtech.com or ask in #prm-dev Slack channel
