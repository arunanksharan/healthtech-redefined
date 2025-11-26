# UI Implementation Guide

**Purpose:** Consolidate UI patterns and provide implementation-ready specifications for all UX epics.
**Tech Stack:** Next.js 14+, Tailwind CSS, shadcn/ui, Zustand, TanStack Query

---

## Table of Contents

1. [Global Application Shell](#global-application-shell)
2. [Navigation Sidebar with FHIR Entities](#navigation-sidebar-with-fhir-entities)
3. [AI Assistant Chat Widget](#ai-assistant-chat-widget)
4. [Data Tables & Lists](#data-tables--lists)
5. [Form Patterns](#form-patterns)
6. [Modal & Panel Patterns](#modal--panel-patterns)
7. [Real-Time Components](#real-time-components)
8. [Mobile Responsive Patterns](#mobile-responsive-patterns)
9. [File Structure](#file-structure)

---

## 1. Global Application Shell

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TOP BAR (64px)                                      │
│  ┌────┐ ┌──────────────────────────────────┐ ┌────┐ ┌────┐ ┌────┐ ┌──────────┐ │
│  │ ≡  │ │ 🔍 Search or ask AI... (⌘K)     │ │ 🔔 │ │ ❓ │ │ ⚙️ │ │ 👤 User  │ │
│  └────┘ └──────────────────────────────────┘ └────┘ └────┘ └────┘ └──────────┘ │
├─────────┬───────────────────────────────────────────────────────┬───────────────┤
│         │                                                       │               │
│ SIDEBAR │                  MAIN CONTENT                         │ CONTEXT PANEL │
│ (240px) │                  (flex-1)                             │ (320px)       │
│         │                                                       │               │
│ [Nav]   │  ┌─────────────────────────────────────────────────┐  │ (Slides in    │
│         │  │                                                 │  │  on selection)│
│         │  │  Page Content                                   │  │               │
│         │  │                                                 │  │               │
│         │  │                                                 │  │               │
│         │  └─────────────────────────────────────────────────┘  │               │
│         │                                                       │               │
├─────────┴───────────────────────────────────────────────────────┴───────────────┤
│                         AI ASSISTANT WIDGET (Fixed)                              │
│                              [Collapsed: FAB]                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```tsx
// src/components/layout/app-shell.tsx
interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { isSidebarCollapsed } = useLayoutStore();
  const { isContextPanelOpen, contextContent } = useContextPanelStore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Top Bar */}
      <TopBar />

      <div className="flex h-[calc(100vh-64px)]">
        {/* Sidebar */}
        <Sidebar collapsed={isSidebarCollapsed} />

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>

        {/* Context Panel (slides in) */}
        {isContextPanelOpen && (
          <ContextPanel>{contextContent}</ContextPanel>
        )}
      </div>

      {/* AI Assistant Widget */}
      <AIAssistantWidget />
    </div>
  );
}
```

---

## 2. Navigation Sidebar with FHIR Entities

### Visual Specification

```
┌─────────────────────────────┐
│ ┌─────────────────────────┐ │
│ │  [Logo]                 │ │
│ │  Surya Hospitals        │ │
│ └─────────────────────────┘ │
│                             │
│ ─────────────────────────── │
│ MAIN                        │
│ ─────────────────────────── │
│                             │
│ ▸ 🏠 Dashboard              │
│ ▸ 📥 Inbox            [12]  │ ← Badge for unread count
│ ▸ 📅 Schedule               │
│                             │
│ ─────────────────────────── │
│ FHIR ENTITIES               │ ← Collapsible section
│ ─────────────────────────── │
│                             │
│ ▸ 👥 Patients               │
│ ▸ 👨‍⚕️ Practitioners          │
│ ▸ 🏢 Organizations          │
│ ▸ 📍 Locations              │
│ ▸ 🗓️ Schedules              │
│ ▸ ⏰ Slots                  │
│ ▸ 📋 Appointments           │
│ ▸ 🏥 Encounters             │
│ ▸ 🔬 Observations           │
│ ▸ 🩺 Conditions             │
│ ▸ 💊 Medications            │
│ ▸ 🧪 DiagnosticReports      │
│                             │
│ ─────────────────────────── │
│ WORKFLOWS                   │
│ ─────────────────────────── │
│                             │
│ ▸ 📊 Analytics              │
│ ▸ 💬 Collaboration          │
│ ▸ 📹 Telehealth             │
│ ▸ 💳 Billing                │
│                             │
│ ─────────────────────────── │
│                             │
│ ┌─────────────────────────┐ │
│ │ 👤 Dr. Sharma           │ │
│ │    Cardiologist    [▼]  │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### Implementation

```tsx
// src/components/layout/sidebar.tsx
const navigationConfig = {
  main: [
    { id: 'dashboard', label: 'Dashboard', icon: Home, href: '/' },
    { id: 'inbox', label: 'Inbox', icon: Inbox, href: '/inbox', badge: 'unreadCount' },
    { id: 'schedule', label: 'Schedule', icon: Calendar, href: '/schedule' },
  ],
  fhirEntities: [
    { id: 'patients', label: 'Patients', icon: Users, href: '/patients' },
    { id: 'practitioners', label: 'Practitioners', icon: UserCog, href: '/practitioners' },
    { id: 'organizations', label: 'Organizations', icon: Building2, href: '/organizations' },
    { id: 'locations', label: 'Locations', icon: MapPin, href: '/locations' },
    { id: 'schedules', label: 'Schedules', icon: CalendarDays, href: '/schedules' },
    { id: 'slots', label: 'Slots', icon: Clock, href: '/slots' },
    { id: 'appointments', label: 'Appointments', icon: ClipboardList, href: '/appointments' },
    { id: 'encounters', label: 'Encounters', icon: Hospital, href: '/encounters' },
    { id: 'observations', label: 'Observations', icon: Microscope, href: '/observations' },
    { id: 'conditions', label: 'Conditions', icon: Stethoscope, href: '/conditions' },
    { id: 'medications', label: 'Medications', icon: Pill, href: '/medications' },
    { id: 'diagnosticReports', label: 'DiagnosticReports', icon: FlaskConical, href: '/diagnostic-reports' },
  ],
  workflows: [
    { id: 'analytics', label: 'Analytics', icon: BarChart3, href: '/analytics' },
    { id: 'collaboration', label: 'Collaboration', icon: MessageSquare, href: '/collaboration' },
    { id: 'telehealth', label: 'Telehealth', icon: Video, href: '/telehealth' },
    { id: 'billing', label: 'Billing', icon: CreditCard, href: '/billing' },
  ],
};

interface SidebarProps {
  collapsed?: boolean;
}

export function Sidebar({ collapsed = false }: SidebarProps) {
  const pathname = usePathname();
  const { data: badges } = useBadgeCounts();

  return (
    <aside
      className={cn(
        "h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700",
        "flex flex-col transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-gray-200">
        <Logo collapsed={collapsed} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <NavSection title="Main" collapsed={collapsed}>
          {navigationConfig.main.map((item) => (
            <NavItem
              key={item.id}
              {...item}
              active={pathname === item.href}
              collapsed={collapsed}
              badge={item.badge ? badges?.[item.badge] : undefined}
            />
          ))}
        </NavSection>

        <NavSection title="FHIR Entities" collapsed={collapsed} collapsible>
          {navigationConfig.fhirEntities.map((item) => (
            <NavItem
              key={item.id}
              {...item}
              active={pathname.startsWith(item.href)}
              collapsed={collapsed}
            />
          ))}
        </NavSection>

        <NavSection title="Workflows" collapsed={collapsed}>
          {navigationConfig.workflows.map((item) => (
            <NavItem
              key={item.id}
              {...item}
              active={pathname.startsWith(item.href)}
              collapsed={collapsed}
            />
          ))}
        </NavSection>
      </nav>

      {/* User Profile */}
      <UserProfileMenu collapsed={collapsed} />
    </aside>
  );
}
```

### NavItem Component

```tsx
// src/components/layout/nav-item.tsx
interface NavItemProps {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  active?: boolean;
  collapsed?: boolean;
  badge?: number;
}

export function NavItem({ label, icon: Icon, href, active, collapsed, badge }: NavItemProps) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 px-3 py-2 mx-2 rounded-md text-sm font-medium",
        "transition-colors duration-150",
        "hover:bg-gray-100 dark:hover:bg-gray-700",
        active && "bg-blue-50 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400",
        active && "border-l-2 border-blue-600"
      )}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1">{label}</span>
          {badge !== undefined && badge > 0 && (
            <Badge variant="secondary" className="ml-auto">
              {badge > 99 ? '99+' : badge}
            </Badge>
          )}
        </>
      )}
    </Link>
  );
}
```

---

## 3. AI Assistant Chat Widget

### Visual Specification

```
COLLAPSED STATE (FAB):
┌──────┐
│ 🤖 ✨│  ← Floating action button, bottom-right
└──────┘

EXPANDED STATE:
┌─────────────────────────────────────────┐
│ 🤖 AI Assistant              [_] [✕]   │ ← Header with minimize/close
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🤖 How can I help you today?       │ │ ← Chat history area
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 👤 Book an appointment for patient │ │ ← User message
│ │    9844111173 with Dr. Sharma      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🤖 I'll help you book that.        │ │ ← AI response with action card
│ │                                     │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ 📅 BOOKING PREVIEW              │ │ │ ← Ghost card
│ │ │                                 │ │ │
│ │ │ Patient: Rajesh Kumar      [✓] │ │ │
│ │ │ Doctor:  Dr. Rohit Sharma  [✓] │ │ │
│ │ │ Time:    Today, 2:00 PM    [✓] │ │ │
│ │ │                                 │ │ │
│ │ │ [Cancel]  [Confirm Booking]    │ │ │
│ │ └─────────────────────────────────┘ │ │
│ └─────────────────────────────────────┘ │
│                                         │
├─────────────────────────────────────────┤
│ Suggested:                              │ ← Quick suggestions
│ [📅 Book Appt] [🔍 Find Patient] [📊]  │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ Ask anything...        [🎤] [→]    │ │ ← Input with mic toggle
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Implementation

```tsx
// src/components/ai-assistant/ai-assistant-widget.tsx
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actionCard?: ActionCard;
}

interface ActionCard {
  type: 'booking' | 'prescription' | 'referral' | 'chart' | 'table';
  data: Record<string, unknown>;
  actions: { label: string; action: string; variant?: 'primary' | 'secondary' }[];
}

export function AIAssistantWidget() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { mutate: sendMessage } = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message, context: getCurrentContext() }),
      });
      return response.json();
    },
    onSuccess: (data) => {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        actionCard: data.actionCard,
      }]);
    },
  });

  // Collapsed FAB
  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className={cn(
          "fixed bottom-6 right-6 z-50",
          "h-14 w-14 rounded-full",
          "bg-blue-600 hover:bg-blue-700 text-white",
          "shadow-lg hover:shadow-xl",
          "flex items-center justify-center",
          "transition-all duration-200"
        )}
      >
        <Bot className="h-6 w-6" />
        <span className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse" />
      </button>
    );
  }

  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50",
        "w-96 bg-white dark:bg-gray-800 rounded-xl shadow-2xl",
        "border border-gray-200 dark:border-gray-700",
        "flex flex-col",
        isMinimized ? "h-14" : "h-[600px]"
      )}
    >
      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-blue-600" />
          <span className="font-semibold">AI Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setIsMinimized(!isMinimized)} className="p-1 hover:bg-gray-100 rounded">
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </button>
          <button onClick={() => setIsExpanded(false)} className="p-1 hover:bg-gray-100 rounded">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <WelcomeMessage />
            ) : (
              messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))
            )}
            {isLoading && <TypingIndicator />}
          </div>

          {/* Quick Suggestions */}
          <div className="px-4 py-2 border-t border-gray-100">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {quickSuggestions.map((suggestion) => (
                <button
                  key={suggestion.label}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="shrink-0 px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
                >
                  {suggestion.icon} {suggestion.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                placeholder="Ask anything..."
                className="flex-1 bg-transparent outline-none text-sm"
              />
              <button
                onClick={() => setIsListening(!isListening)}
                className={cn(
                  "p-2 rounded-full transition-colors",
                  isListening ? "bg-red-100 text-red-600 animate-pulse" : "hover:bg-gray-200"
                )}
              >
                {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </button>
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || isLoading}
                className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">⌘K</kbd> anywhere to open
            </p>
          </div>
        </>
      )}
    </div>
  );
}
```

### Chat Message Component

```tsx
// src/components/ai-assistant/chat-message.tsx
interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div className={cn(
        "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
        isUser ? "bg-blue-100" : "bg-gray-100"
      )}>
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div className={cn(
        "max-w-[80%] space-y-2",
        isUser && "text-right"
      )}>
        <div className={cn(
          "px-4 py-2 rounded-2xl text-sm",
          isUser ? "bg-blue-600 text-white rounded-br-md" : "bg-gray-100 dark:bg-gray-700 rounded-bl-md"
        )}>
          {message.content}
        </div>

        {/* Action Card (for AI responses) */}
        {message.actionCard && (
          <ActionCardRenderer card={message.actionCard} />
        )}

        <span className="text-xs text-gray-400">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
```

### Action Card (Ghost Card) Component

```tsx
// src/components/ai-assistant/action-card.tsx
interface ActionCardRendererProps {
  card: ActionCard;
}

export function ActionCardRenderer({ card }: ActionCardRendererProps) {
  switch (card.type) {
    case 'booking':
      return <BookingPreviewCard data={card.data} actions={card.actions} />;
    case 'prescription':
      return <PrescriptionPreviewCard data={card.data} actions={card.actions} />;
    case 'chart':
      return <ChartPreviewCard data={card.data} actions={card.actions} />;
    default:
      return <GenericActionCard data={card.data} actions={card.actions} />;
  }
}

function BookingPreviewCard({ data, actions }: { data: any; actions: any[] }) {
  return (
    <div className="bg-white dark:bg-gray-800 border rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-blue-600">
        <Calendar className="h-4 w-4" />
        BOOKING PREVIEW
      </div>

      <div className="space-y-2">
        <EntityTag
          icon={<User className="h-3 w-3" />}
          label="Patient"
          value={data.patient.name}
          confidence={data.patient.confidence}
          editable
        />
        <EntityTag
          icon={<UserCog className="h-3 w-3" />}
          label="Doctor"
          value={data.practitioner.name}
          confidence={data.practitioner.confidence}
          editable
        />
        <EntityTag
          icon={<Clock className="h-3 w-3" />}
          label="Time"
          value={formatDateTime(data.appointmentTime)}
          confidence={data.time.confidence}
          editable
        />
      </div>

      <div className="flex gap-2 pt-2 border-t">
        {actions.map((action) => (
          <Button
            key={action.action}
            variant={action.variant === 'primary' ? 'default' : 'outline'}
            size="sm"
            className="flex-1"
          >
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
```

### Entity Tag Component

```tsx
// src/components/ai-assistant/entity-tag.tsx
interface EntityTagProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  confidence?: number;
  editable?: boolean;
  onEdit?: () => void;
}

export function EntityTag({ icon, label, value, confidence = 100, editable, onEdit }: EntityTagProps) {
  const isLowConfidence = confidence < 80;

  return (
    <div className="flex items-center justify-between text-sm">
      <div className="flex items-center gap-2 text-gray-500">
        {icon}
        <span>{label}:</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-medium">{value}</span>
        {confidence >= 80 ? (
          <CheckCircle className="h-4 w-4 text-green-500" />
        ) : (
          <AlertCircle className="h-4 w-4 text-yellow-500" />
        )}
        {editable && (
          <button onClick={onEdit} className="p-1 hover:bg-gray-100 rounded">
            <ChevronDown className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## 4. Data Tables & Lists

### Visual Specification

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PAGE TITLE                                                         [+ Add New]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔍 Search...           │ [Filter ▼] [Columns ▼] [Export ▼]                 │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│ [All] [Active: 125] [Pending: 12] [Inactive: 8]                ← Status tabs   │
│                                                                                 │
│ ┌─────┬───────────────────────┬────────────────┬──────────────┬──────┬───────┐ │
│ │ ☐   │ Name               ↓  │ Status         │ Created      │ Type │ ⋮     │ │
│ ├─────┼───────────────────────┼────────────────┼──────────────┼──────┼───────┤ │
│ │ ☐   │ 👤 John Doe           │ 🟢 Active      │ Nov 25, 2024 │ New  │ ⋮     │ │
│ │     │    john@email.com     │                │              │      │       │ │
│ ├─────┼───────────────────────┼────────────────┼──────────────┼──────┼───────┤ │
│ │ ☐   │ 👤 Jane Smith         │ 🟡 Pending     │ Nov 24, 2024 │ F/U  │ ⋮     │ │
│ │     │    jane@email.com     │                │              │      │       │ │
│ └─────┴───────────────────────┴────────────────┴──────────────┴──────┴───────┘ │
│                                                                                 │
│ ☑️ 2 selected  [Bulk Actions ▼]                                                │
│                                                                                 │
│ Showing 1-10 of 145                                             [◀ 1 2 3 ... ▶]│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```tsx
// src/components/data-table/data-table.tsx
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  searchPlaceholder?: string;
  searchFields?: (keyof T)[];
  filters?: FilterConfig[];
  statusTabs?: StatusTab[];
  bulkActions?: BulkAction[];
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
}

export function DataTable<T>({
  data,
  columns,
  searchPlaceholder = "Search...",
  searchFields,
  filters,
  statusTabs,
  bulkActions,
  onRowClick,
  isLoading,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [activeStatus, setActiveStatus] = useState<string | null>(null);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder={searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          {filters && <FilterDropdown filters={filters} />}
          <ColumnVisibilityDropdown table={table} />
          <ExportDropdown data={data} columns={columns} />
        </div>
      </div>

      {/* Status Tabs */}
      {statusTabs && (
        <div className="flex gap-2">
          {statusTabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveStatus(tab.value)}
              className={cn(
                "px-3 py-1.5 text-sm rounded-md transition-colors",
                activeStatus === tab.value
                  ? "bg-blue-100 text-blue-700"
                  : "hover:bg-gray-100"
              )}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1.5 text-gray-500">({tab.count})</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border border-gray-200 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.id} className="bg-gray-50">
                  {column.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableSkeleton columns={columns.length} rows={5} />
            ) : (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  onClick={() => onRowClick?.(row.original)}
                  className="cursor-pointer hover:bg-gray-50"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {selectedRows.size > 0 && (
            <>
              <span className="text-sm text-gray-500">
                {selectedRows.size} selected
              </span>
              <BulkActionsDropdown actions={bulkActions} selectedIds={[...selectedRows]} />
            </>
          )}
        </div>
        <Pagination table={table} />
      </div>
    </div>
  );
}
```

---

## 5. Form Patterns

### Visual Specification - Inline Entity Creation

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ CREATE PATIENT                                                           [✕]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ Personal Information                                                            │
│ ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│ ┌─────────────────────────────┐  ┌─────────────────────────────┐               │
│ │ First Name *                │  │ Last Name *                 │               │
│ │ [John                     ] │  │ [Doe                      ] │               │
│ └─────────────────────────────┘  └─────────────────────────────┘               │
│                                                                                 │
│ ┌─────────────────────────────┐  ┌──────────────┐  ┌──────────────┐            │
│ │ Date of Birth *             │  │ Gender *     │  │ Blood Type   │            │
│ │ [📅 01/15/1985            ] │  │ [Male    ▼]  │  │ [A+       ▼] │            │
│ └─────────────────────────────┘  └──────────────┘  └──────────────┘            │
│                                                                                 │
│ Contact Information                                                             │
│ ──────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│ ┌─────────────────────────────┐  ┌─────────────────────────────┐               │
│ │ Phone Number *              │  │ Email                       │               │
│ │ [🇮🇳 +91] [98441 11173    ] │  │ [john.doe@email.com       ] │               │
│ └─────────────────────────────┘  └─────────────────────────────┘               │
│                                                                                 │
│ ┌───────────────────────────────────────────────────────────────────────────┐  │
│ │ Address                                                                   │  │
│ │ [123 Main Street, Whitefield                                            ] │  │
│ └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│ ┌──────────────┐  ┌──────────────────────────────┐  ┌──────────────┐           │
│ │ City *       │  │ State *                      │  │ PIN Code *   │           │
│ │ [Bangalore ] │  │ [Karnataka                ▼] │  │ [560066    ] │           │
│ └──────────────┘  └──────────────────────────────┘  └──────────────┘           │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                         [Cancel]    [Create Patient]            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```tsx
// src/components/forms/patient-form.tsx
const patientSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  dateOfBirth: z.date({ required_error: 'Date of birth is required' }),
  gender: z.enum(['male', 'female', 'other']),
  bloodType: z.string().optional(),
  phone: z.string().min(10, 'Valid phone number required'),
  email: z.string().email().optional().or(z.literal('')),
  address: z.string().optional(),
  city: z.string().min(1, 'City is required'),
  state: z.string().min(1, 'State is required'),
  pinCode: z.string().min(6, 'Valid PIN code required'),
});

type PatientFormData = z.infer<typeof patientSchema>;

interface PatientFormProps {
  onSubmit: (data: PatientFormData) => void;
  onCancel: () => void;
  defaultValues?: Partial<PatientFormData>;
  isLoading?: boolean;
}

export function PatientForm({ onSubmit, onCancel, defaultValues, isLoading }: PatientFormProps) {
  const form = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues,
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Personal Information */}
        <FormSection title="Personal Information">
          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="firstName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>First Name *</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="lastName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Last Name *</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <FormField
              control={form.control}
              name="dateOfBirth"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Date of Birth *</FormLabel>
                  <DatePicker value={field.value} onChange={field.onChange} />
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="gender"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Gender *</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Male</SelectItem>
                      <SelectItem value="female">Female</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="bloodType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Blood Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {bloodTypes.map((type) => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
          </div>
        </FormSection>

        {/* Contact Information */}
        <FormSection title="Contact Information">
          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone Number *</FormLabel>
                  <PhoneInput {...field} defaultCountry="IN" />
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <FormField
            control={form.control}
            name="address"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Address</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
              </FormItem>
            )}
          />

          <div className="grid grid-cols-3 gap-4">
            <FormField control={form.control} name="city" render={/* ... */} />
            <FormField control={form.control} name="state" render={/* ... */} />
            <FormField control={form.control} name="pinCode" render={/* ... */} />
          </div>
        </FormSection>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Create Patient
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

---

## 6. Modal & Panel Patterns

### Sheet/Side Panel (Context Panel)

```tsx
// src/components/panels/context-panel.tsx
interface ContextPanelProps {
  children: React.ReactNode;
  title?: string;
  onClose: () => void;
  width?: 'sm' | 'md' | 'lg';
}

export function ContextPanel({ children, title, onClose, width = 'md' }: ContextPanelProps) {
  const widthClasses = {
    sm: 'w-80',
    md: 'w-96',
    lg: 'w-[480px]',
  };

  return (
    <div
      className={cn(
        "fixed right-0 top-16 h-[calc(100vh-64px)]",
        "bg-white dark:bg-gray-800 border-l border-gray-200",
        "shadow-xl overflow-hidden",
        "animate-in slide-in-from-right duration-200",
        widthClasses[width]
      )}
    >
      {/* Header */}
      {title && (
        <div className="h-14 px-4 flex items-center justify-between border-b border-gray-200">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Content */}
      <div className="h-full overflow-y-auto p-4">
        {children}
      </div>
    </div>
  );
}
```

### Modal Dialog

```tsx
// src/components/dialogs/confirm-dialog.tsx
interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'default' | 'destructive';
  onConfirm: () => void;
  isLoading?: boolean;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  isLoading,
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className={cn(variant === 'destructive' && "bg-red-600 hover:bg-red-700")}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

---

## 7. Real-Time Components

### WebSocket Connection Manager

```tsx
// src/hooks/use-realtime.ts
interface UseRealtimeOptions {
  channel: string;
  onMessage: (data: unknown) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useRealtime({ channel, onMessage, onConnect, onDisconnect }: UseRealtimeOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/${channel}`);

    ws.onopen = () => {
      setIsConnected(true);
      onConnect?.();
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onclose = () => {
      setIsConnected(false);
      onDisconnect?.();
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [channel]);

  const send = useCallback((data: unknown) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);

  return { isConnected, send };
}
```

### Live Feed Item Animation

```tsx
// src/components/feed/feed-item.tsx
interface FeedItemProps {
  item: FeedItem;
  isNew?: boolean;
  onClick: () => void;
}

export function FeedItem({ item, isNew, onClick }: FeedItemProps) {
  return (
    <motion.div
      initial={isNew ? { opacity: 0, y: -20 } : false}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-4 border rounded-lg cursor-pointer transition-all",
        "hover:shadow-md hover:border-blue-200",
        item.status === 'unread' && "border-l-4 border-l-blue-500 bg-blue-50/50",
        item.priority === 'high' && "border-l-red-500 bg-red-50/30",
        isNew && "animate-pulse"
      )}
      onClick={onClick}
    >
      {/* Item content */}
    </motion.div>
  );
}
```

---

## 8. Mobile Responsive Patterns

### Mobile Navigation

```tsx
// src/components/layout/mobile-nav.tsx
export function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { href: '/', icon: Home, label: 'Home' },
    { href: '/schedule', icon: Calendar, label: 'Schedule' },
    { href: '/inbox', icon: Inbox, label: 'Inbox', badge: true },
    { href: '/patients', icon: Users, label: 'Patients' },
    { href: '/more', icon: Menu, label: 'More' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 md:hidden">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center justify-center flex-1 h-full",
              "text-xs transition-colors",
              pathname === item.href ? "text-blue-600" : "text-gray-500"
            )}
          >
            <item.icon className="h-5 w-5" />
            <span className="mt-1">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
```

### Responsive Layout Hook

```tsx
// src/hooks/use-media-query.ts
export function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

export function useIsMobile() {
  return useMediaQuery('(max-width: 768px)');
}

export function useIsTablet() {
  return useMediaQuery('(min-width: 768px) and (max-width: 1024px)');
}
```

---

## 9. File Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # Auth routes group
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/              # Dashboard routes group
│   │   │   ├── layout.tsx            # AppShell wrapper
│   │   │   ├── page.tsx              # Dashboard home
│   │   │   ├── inbox/
│   │   │   ├── patients/
│   │   │   │   ├── page.tsx          # List view
│   │   │   │   └── [id]/page.tsx     # Detail view
│   │   │   ├── practitioners/
│   │   │   ├── organizations/
│   │   │   ├── locations/
│   │   │   ├── appointments/
│   │   │   ├── schedule/
│   │   │   ├── analytics/
│   │   │   ├── telehealth/
│   │   │   ├── billing/
│   │   │   └── settings/
│   │   └── api/                      # API routes
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   ├── layout/                   # Layout components
│   │   │   ├── app-shell.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── nav-item.tsx
│   │   │   ├── top-bar.tsx
│   │   │   ├── context-panel.tsx
│   │   │   └── mobile-nav.tsx
│   │   ├── ai-assistant/             # AI Copilot components
│   │   │   ├── ai-assistant-widget.tsx
│   │   │   ├── chat-message.tsx
│   │   │   ├── action-card.tsx
│   │   │   ├── entity-tag.tsx
│   │   │   └── voice-input.tsx
│   │   ├── data-display/             # Data presentation
│   │   │   ├── data-table.tsx
│   │   │   ├── stat-card.tsx
│   │   │   ├── timeline.tsx
│   │   │   └── chart-wrapper.tsx
│   │   ├── forms/                    # Form components
│   │   │   ├── patient-form.tsx
│   │   │   ├── practitioner-form.tsx
│   │   │   ├── appointment-form.tsx
│   │   │   └── ...
│   │   ├── dialogs/                  # Modal dialogs
│   │   │   ├── confirm-dialog.tsx
│   │   │   └── ...
│   │   └── healthcare/               # Domain-specific
│   │       ├── patient-banner.tsx
│   │       ├── vital-signs.tsx
│   │       ├── medication-card.tsx
│   │       └── allergy-badge.tsx
│   │
│   ├── hooks/                        # Custom hooks
│   │   ├── use-realtime.ts
│   │   ├── use-media-query.ts
│   │   └── ...
│   │
│   ├── stores/                       # Zustand stores
│   │   ├── layout-store.ts
│   │   ├── inbox-store.ts
│   │   └── ...
│   │
│   ├── services/                     # API services
│   │   ├── api-client.ts
│   │   ├── patients.ts
│   │   ├── practitioners.ts
│   │   └── ...
│   │
│   ├── lib/                          # Utilities
│   │   ├── utils.ts
│   │   └── cn.ts
│   │
│   └── styles/
│       ├── globals.css
│       └── tokens.css
│
├── public/
├── tailwind.config.ts
├── next.config.js
└── package.json
```

---

## Key Design Principles

### 1. Modern B2B Healthcare Design
- **Clean, minimal interfaces** - White space, clear hierarchy
- **Contextual information density** - Show what's needed, hide what's not
- **Progressive disclosure** - Details on demand via panels/modals
- **Status-driven colors** - Consistent semantic colors across the app

### 2. Healthcare-Specific Patterns
- **Patient context always visible** - Banner with allergies, alerts
- **HIPAA-aware UI** - Session timeouts, audit indicators
- **Clinical color coding** - Red for critical, yellow for warnings
- **Quick actions** - Common tasks always accessible

### 3. Accessibility Requirements
- **WCAG 2.1 AA compliance**
- **Keyboard navigation** throughout
- **Screen reader support** with proper ARIA labels
- **High contrast mode** support
- **Reduced motion** respects `prefers-reduced-motion`

---

**Document Owner:** Frontend Architecture Team
**Last Updated:** November 26, 2024
**Review Cycle:** Every Sprint
