# EPIC-UX-001: Design System & Foundation

**Priority:** P0 | **Estimated Effort:** 3 weeks | **Dependencies:** None
**Theme:** Establish the visual foundation and component library for the entire PRM platform

---

## Executive Summary

This epic establishes the foundational design system that powers every screen, component, and interaction in the PRM platform. It defines the visual language, component library, theming infrastructure, and accessibility standards that ensure consistency, scalability, and a world-class user experience across all modules.

---

## Strategic Objectives

1. **Visual Consistency** - Single source of truth for all UI components
2. **Developer Velocity** - Pre-built components accelerate feature development
3. **Accessibility First** - WCAG 2.1 AA compliance from the ground up
4. **Healthcare Compliance** - HIPAA-aware components with audit trails
5. **Multi-Tenant Theming** - White-label capability for enterprise clients

---

## Tech Stack Alignment

- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS 3.4+
- **Component Library:** shadcn/ui (customized)
- **State Management:** Zustand + TanStack Query
- **Authentication:** NextAuth.js
- **Icons:** Lucide React + Custom healthcare icons
- **Charts:** Recharts / Tremor
- **Forms:** React Hook Form + Zod validation

---

## User Journeys

### Journey 1.1: First-Time User Onboarding

**Persona:** Hospital Administrator setting up a new tenant

**Flow:**
```
Landing Page → Organization Setup Wizard → Branding Configuration →
Department Setup → User Invitation → Dashboard Preview → Go Live
```

**Detailed Steps:**

1. **Welcome Screen**
   - Clean, minimal hero section with product value proposition
   - "Get Started" CTA with organization type selection
   - Social proof: logos of healthcare partners

2. **Organization Setup Wizard**
   - Step 1: Organization name, type (hospital/clinic/practice), size
   - Step 2: Primary contact information
   - Step 3: Logo upload with automatic color extraction
   - Step 4: Theme preference (light/dark/system)
   - Progress indicator showing completion percentage

3. **Branding Configuration**
   - Live preview panel showing how their brand will appear
   - Primary/secondary color picker with contrast checker
   - Font selection from healthcare-appropriate options
   - Logo placement options (header/sidebar/both)

4. **Department Setup**
   - Drag-and-drop department ordering
   - Pre-populated healthcare departments (Cardiology, Orthopedics, etc.)
   - Custom department creation with icon selection

5. **User Invitation**
   - Bulk invite via CSV upload
   - Role assignment dropdown (Admin, Doctor, Nurse, Receptionist)
   - Email preview before sending

6. **Dashboard Preview**
   - Interactive tour highlighting key features
   - "Skip tour" option for experienced users
   - Contextual tooltips on first interaction

---

### Journey 1.2: Theme Customization

**Persona:** IT Administrator customizing white-label appearance

**Flow:**
```
Settings → Appearance → Theme Editor → Preview → Save & Publish
```

**Detailed Steps:**

1. **Access Theme Editor**
   - Navigate via Settings > Appearance
   - View current theme preview

2. **Color Customization**
   - Primary brand color with color picker
   - Secondary/accent colors
   - Semantic colors (success, warning, error, info)
   - Automatic contrast ratio calculation
   - "Reset to defaults" option

3. **Typography Settings**
   - Heading font family selection
   - Body font family selection
   - Base font size slider (14px - 18px)
   - Line height adjustment

4. **Component Customization**
   - Border radius slider (none, sm, md, lg, full)
   - Shadow intensity (none, subtle, medium, prominent)
   - Button style (solid, outline, ghost)

5. **Live Preview**
   - Real-time preview of all changes
   - Device preview (desktop, tablet, mobile)
   - Dark mode toggle to verify both themes

6. **Save & Publish**
   - Save as draft for review
   - Publish to all users
   - Rollback to previous version

---

### Journey 1.3: Responsive Layout Navigation

**Persona:** Any user navigating across devices

**Flow:**
```
Desktop (Full Sidebar) → Tablet (Collapsed Sidebar) → Mobile (Bottom Nav)
```

**Desktop Experience (>1280px):**
- Three-column layout: Sidebar (240px) | Main Content | Context Panel (320px)
- Sidebar always visible with full labels
- Context panel slides in/out based on selection

**Tablet Experience (768px - 1279px):**
- Two-column layout: Collapsed Sidebar (64px icons only) | Main Content
- Sidebar expands on hover
- Context panel appears as overlay

**Mobile Experience (<768px):**
- Single column with bottom navigation bar
- 5 primary nav items (Home, Patients, Schedule, Messages, More)
- Full-screen modals for detail views
- Pull-to-refresh for lists

---

## Component Specifications

### Core Components

#### 1. Navigation Sidebar
```
┌─────────────────────────────┐
│  [Logo]                     │
│  [Tenant Name]        [◀▶]  │
├─────────────────────────────┤
│  🏠 Dashboard               │
│  📥 Omni-Inbox         [12] │
│  👥 Patients                │
│  👨‍⚕️ Practitioners          │
│  🏢 Organization            │
│  📅 Schedule                │
│  💬 Messages           [3]  │
│  📊 Analytics               │
│  ⚙️ Settings                │
├─────────────────────────────┤
│  [User Avatar]              │
│  [Name]                     │
│  [Role]               [⚙️]  │
└─────────────────────────────┘
```

**States:**
- Default: 240px expanded
- Collapsed: 64px icons only
- Hover: Expand labels on collapsed
- Active: Highlighted background + left border accent

#### 2. Top Bar
```
┌──────────────────────────────────────────────────────────────┐
│ [≡] [Breadcrumb / Page Title]  [🔍 Search...] [🔔 4] [👤]   │
└──────────────────────────────────────────────────────────────┘
```

**Features:**
- Mobile menu toggle (hamburger)
- Dynamic breadcrumb navigation
- Global search with Cmd+K shortcut
- Notification bell with unread count
- User avatar with dropdown menu

#### 3. Data Table
```
┌──────────────────────────────────────────────────────────────┐
│ [Filter ▼] [Column ▼] [Export ▼]        [🔍 Search] [+ New] │
├──────────────────────────────────────────────────────────────┤
│ ☐ │ Name ▼      │ Status    │ Date       │ Actions         │
├───┼─────────────┼───────────┼────────────┼─────────────────┤
│ ☐ │ John Doe    │ 🟢 Active │ Nov 25     │ [View] [Edit]   │
│ ☐ │ Jane Smith  │ 🟡 Pending│ Nov 24     │ [View] [Edit]   │
├──────────────────────────────────────────────────────────────┤
│ [Select All] [Bulk Actions ▼]     Showing 1-10 of 234 [◀ ▶] │
└──────────────────────────────────────────────────────────────┘
```

**Features:**
- Sortable columns with visual indicators
- Multi-select with bulk actions
- Inline row actions
- Pagination with page size options
- Column visibility toggle
- Export to CSV/Excel
- Saved filter presets

#### 4. Form Components
- Text Input (with validation states)
- Select/Dropdown (single and multi-select)
- Date Picker (with range selection)
- Time Picker (with timezone support)
- Phone Input (with country code)
- File Upload (drag-and-drop)
- Rich Text Editor (for clinical notes)
- Signature Pad (for consent forms)

#### 5. Card Components
```
┌─────────────────────────────────────────┐
│ [Icon] Card Title              [⋮ Menu] │
├─────────────────────────────────────────┤
│                                         │
│  Main content area                      │
│                                         │
├─────────────────────────────────────────┤
│ [Secondary Action]    [Primary Action]  │
└─────────────────────────────────────────┘
```

**Variants:**
- Default Card
- Stat Card (with trend indicator)
- Patient Card (avatar, name, status)
- Alert Card (warning, error, info variants)
- Timeline Card (for activity feeds)

#### 6. Modal/Dialog System
```
┌─────────────────────────────────────────────────────────────┐
│                    [Overlay Background]                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Modal Title                                    [✕]    │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  Modal content...                                     │  │
│  │                                                       │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │                    [Cancel]  [Confirm]                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Sizes:** Small (400px), Medium (560px), Large (720px), Full Screen

#### 7. Toast/Notification System
```
┌────────────────────────────────────────┐
│ ✓ Success message text          [✕]   │
└────────────────────────────────────────┘
```

**Types:** Success, Error, Warning, Info, Loading
**Position:** Top-right by default, configurable
**Duration:** Auto-dismiss after 5 seconds (configurable)

---

## Design Tokens

### Color Palette

```css
/* Primary Colors */
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-500: #3b82f6;  /* Main brand color */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;

/* Semantic Colors */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;

/* Healthcare-Specific Colors */
--color-urgent: #dc2626;       /* Critical alerts */
--color-scheduled: #8b5cf6;    /* Appointments */
--color-completed: #059669;    /* Finished tasks */
--color-cancelled: #6b7280;    /* Inactive items */

/* Sentiment Colors (for Zoice/WhatsApp) */
--color-sentiment-positive: #10b981;
--color-sentiment-neutral: #6b7280;
--color-sentiment-negative: #ef4444;
--color-sentiment-frustrated: #f97316;

/* Channel Colors */
--color-channel-voice: #8b5cf6;    /* Zoice calls */
--color-channel-whatsapp: #25d366; /* WhatsApp */
--color-channel-email: #3b82f6;    /* Email */
--color-channel-sms: #06b6d4;      /* SMS */
--color-channel-app: #6366f1;      /* In-app */
```

### Typography Scale

```css
/* Font Families */
--font-heading: 'Inter', system-ui, sans-serif;
--font-body: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px - Captions */
--text-sm: 0.875rem;   /* 14px - Secondary text */
--text-base: 1rem;     /* 16px - Body text */
--text-lg: 1.125rem;   /* 18px - Emphasized */
--text-xl: 1.25rem;    /* 20px - Card titles */
--text-2xl: 1.5rem;    /* 24px - Section headers */
--text-3xl: 1.875rem;  /* 30px - Page titles */
--text-4xl: 2.25rem;   /* 36px - Hero text */

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### Spacing Scale

```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Border Radius

```css
--radius-none: 0;
--radius-sm: 0.25rem;   /* 4px - Buttons */
--radius-md: 0.375rem;  /* 6px - Cards */
--radius-lg: 0.5rem;    /* 8px - Modals */
--radius-xl: 0.75rem;   /* 12px - Large cards */
--radius-2xl: 1rem;     /* 16px - Hero sections */
--radius-full: 9999px;  /* Pills, avatars */
```

### Shadow System

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
```

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

1. **Color Contrast**
   - Normal text: minimum 4.5:1 ratio
   - Large text (18px+): minimum 3:1 ratio
   - UI components: minimum 3:1 ratio
   - Built-in contrast checker in theme editor

2. **Keyboard Navigation**
   - All interactive elements focusable
   - Visible focus indicators (2px ring)
   - Logical tab order
   - Skip-to-content link
   - Escape key closes modals

3. **Screen Reader Support**
   - Semantic HTML elements
   - ARIA labels for icons and buttons
   - Live regions for dynamic content
   - Descriptive link text (no "click here")

4. **Motion & Animation**
   - Respect `prefers-reduced-motion`
   - No auto-playing animations
   - Pause/stop controls for video
   - Smooth scrolling optional

5. **Forms**
   - Associated labels for all inputs
   - Error messages linked to fields
   - Required field indicators
   - Clear validation feedback

---

## Healthcare-Specific Components

### 1. Patient Identifier Banner
```
┌─────────────────────────────────────────────────────────────┐
│ 👤 John Doe  │ DOB: 01/15/1980 │ MRN: 12345 │ ⚠️ Allergies │
└─────────────────────────────────────────────────────────────┘
```
- Always visible when viewing patient context
- Red alert for critical allergies
- Quick access to demographics

### 2. Medication Display
```
┌─────────────────────────────────────────────────────────────┐
│ 💊 Metformin 500mg                                          │
│    Take 1 tablet by mouth twice daily with meals           │
│    Qty: 60 | Refills: 3 | Prescribed: Nov 25, 2024         │
└─────────────────────────────────────────────────────────────┘
```

### 3. Vital Signs Card
```
┌─────────────────────────────────────────────────────────────┐
│ Vital Signs                              Last: 2 hours ago │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ BP          │ HR          │ Temp        │ SpO2            │
│ 120/80 mmHg │ 72 bpm      │ 98.6°F      │ 98%             │
│ 🟢 Normal   │ 🟢 Normal   │ 🟢 Normal   │ 🟢 Normal       │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

### 4. HIPAA-Aware Components
- Session timeout warning (5 min before)
- "Break the glass" confirmation for sensitive data
- Audit trail indicator (viewing logged)
- Emergency access mode (documented override)

---

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                    # Base shadcn components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   ├── layout/                # Layout components
│   │   │   ├── sidebar.tsx
│   │   │   ├── topbar.tsx
│   │   │   ├── main-layout.tsx
│   │   │   └── mobile-nav.tsx
│   │   ├── data-display/          # Data presentation
│   │   │   ├── data-table.tsx
│   │   │   ├── stat-card.tsx
│   │   │   ├── timeline.tsx
│   │   │   └── chart-wrapper.tsx
│   │   ├── forms/                 # Form components
│   │   │   ├── form-field.tsx
│   │   │   ├── phone-input.tsx
│   │   │   ├── date-picker.tsx
│   │   │   └── file-upload.tsx
│   │   └── healthcare/            # Domain-specific
│   │       ├── patient-banner.tsx
│   │       ├── vital-signs.tsx
│   │       ├── medication-card.tsx
│   │       └── allergy-badge.tsx
│   ├── styles/
│   │   ├── globals.css            # Global styles
│   │   ├── tokens.css             # Design tokens
│   │   └── theme-provider.tsx     # Theme context
│   └── lib/
│       ├── utils.ts               # Utility functions
│       └── cn.ts                  # Class name merger
├── tailwind.config.ts             # Tailwind configuration
└── components.json                # shadcn/ui config
```

---

## Acceptance Criteria

### AC-1: Component Library
- [ ] All base shadcn/ui components customized with healthcare theme
- [ ] Storybook documentation for each component
- [ ] Unit tests for component functionality
- [ ] Accessibility audit passing

### AC-2: Theming System
- [ ] Light and dark mode fully implemented
- [ ] Theme editor functional in settings
- [ ] CSS custom properties for all design tokens
- [ ] Multi-tenant theme isolation working

### AC-3: Responsive Design
- [ ] Desktop layout (>1280px) functional
- [ ] Tablet layout (768-1279px) functional
- [ ] Mobile layout (<768px) functional
- [ ] Touch-friendly interactions on mobile

### AC-4: Accessibility
- [ ] WCAG 2.1 AA audit passing
- [ ] Keyboard navigation complete
- [ ] Screen reader testing complete
- [ ] Color contrast validation passing

### AC-5: Performance
- [ ] Core Web Vitals passing
- [ ] Component lazy loading implemented
- [ ] Bundle size under 200KB initial
- [ ] No layout shifts (CLS < 0.1)

---

## API Integration Points

This epic interfaces with:
- **Tenant Service:** `/api/v1/prm/tenants` for branding configuration
- **Auth Service:** `/api/v1/prm/auth` for user context
- **User Preferences:** Local storage + server sync for theme preferences

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Component bloat | Regular bundle analysis, tree shaking |
| Theme inconsistency | Design review process, visual regression tests |
| Accessibility gaps | Automated a11y testing in CI/CD |
| Mobile performance | Performance budgets, lighthouse CI |

---

## Success Metrics

- Component reuse rate: >80% across features
- Lighthouse accessibility score: >95
- Designer-developer handoff time: <1 day
- New feature development time: 30% faster with component library

---

**Document Owner:** Frontend Architecture Team
**Last Updated:** November 25, 2024
**Review Cycle:** Every PI Planning
