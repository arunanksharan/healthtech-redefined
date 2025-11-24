# EPIC-014: Patient Portal Platform
**Epic ID:** EPIC-014
**Priority:** P0
**Estimated Story Points:** 89
**Projected Timeline:** Weeks 14-15 (Sprint 4.1-4.2)
**Squad:** Healthcare Team

---

## 📋 Epic Overview

### Business Value Statement
The Patient Portal Platform empowers patients with 24/7 self-service access to their health information, appointment management, secure messaging, and healthcare services. By reducing administrative calls by 60%, increasing patient engagement by 75%, and improving satisfaction scores by 40%, this comprehensive portal transforms the patient experience while reducing operational costs by 35% through automated self-service capabilities.

### Strategic Objectives
1. **Patient Empowerment:** Provide complete access to health records and services
2. **Self-Service Excellence:** Enable 80% of routine tasks through self-service
3. **Care Coordination:** Facilitate seamless patient-provider communication
4. **Financial Transparency:** Offer clear billing and payment options
5. **Health Management:** Support proactive health tracking and education
6. **Family Access:** Enable secure proxy access for caregivers and family members

### Key Stakeholders
- **Primary:** Patients, families, caregivers, patient experience teams
- **Secondary:** Providers, billing department, IT support, registration staff
- **External:** Insurance companies, pharmacies, lab partners, regulatory bodies

---

## 🎯 Success Criteria & KPIs

### Business Metrics
- 75% patient portal adoption rate
- 60% reduction in administrative phone calls
- 80% of appointments booked online
- 50% reduction in payment collection time
- 40% increase in patient satisfaction scores
- 35% operational cost reduction

### Technical Metrics
- Support for 100,000+ concurrent users
- < 2 second page load time
- 99.9% uptime availability
- < 100ms API response time
- Mobile responsiveness on all devices
- WCAG 2.1 AA accessibility compliance

### User Experience Metrics
- < 3 clicks to complete common tasks
- 90% task completion rate
- < 2 minutes for account registration
- 95% successful login rate
- Support for 15+ languages
- 4.5+ app store rating

---

## 📊 User Stories & Acceptance Criteria

### US-14.1: Patient Registration & Onboarding
**As a** new patient
**I want to** create and verify my portal account easily
**So that I can** access my health information and services online

#### Acceptance Criteria:
1. **Registration Process:**
   - [ ] Email-based registration with verification
   - [ ] SMS verification option
   - [ ] Social login (Google, Apple, Microsoft)
   - [ ] Identity verification against medical records
   - [ ] Secure password requirements with strength indicator
   - [ ] Two-factor authentication setup

2. **Profile Setup:**
   - [ ] Demographic information collection
   - [ ] Insurance information entry
   - [ ] Emergency contact management
   - [ ] Communication preferences selection
   - [ ] Health history questionnaire
   - [ ] Document upload (ID, insurance cards)

3. **Onboarding Experience:**
   - [ ] Interactive portal tour
   - [ ] Feature highlights and tips
   - [ ] Personalized dashboard setup
   - [ ] Mobile app download prompt
   - [ ] Notification preferences configuration
   - [ ] Help resources and tutorials

#### Story Points: 13
#### Priority: P0

---

### US-14.2: Health Records Access
**As a** patient
**I want to** view all my medical records in one place
**So that I can** track my health history and share with other providers

#### Acceptance Criteria:
1. **Medical Records Display:**
   - [ ] Visit summaries and clinical notes
   - [ ] Lab results with trends and graphs
   - [ ] Imaging reports with viewer integration
   - [ ] Medication list with instructions
   - [ ] Immunization records
   - [ ] Allergy and problem lists

2. **Document Management:**
   - [ ] Download records in PDF format
   - [ ] Print-friendly layouts
   - [ ] Share records via secure link
   - [ ] Upload external medical records
   - [ ] Request record amendments
   - [ ] Track disclosure history

3. **Data Visualization:**
   - [ ] Health metrics trending (vitals, labs)
   - [ ] Timeline view of medical history
   - [ ] Filterable record categories
   - [ ] Search functionality across records
   - [ ] Comparison of results over time
   - [ ] Preventive care tracker

#### Story Points: 21
#### Priority: P0

---

### US-14.3: Appointment Management
**As a** patient
**I want to** book, reschedule, and manage appointments online
**So that I can** control my healthcare schedule conveniently

#### Acceptance Criteria:
1. **Appointment Booking:**
   - [ ] Real-time availability display
   - [ ] Provider and location selection
   - [ ] Appointment type selection
   - [ ] Reason for visit entry
   - [ ] Insurance verification
   - [ ] Estimated wait time display

2. **Scheduling Features:**
   - [ ] Reschedule existing appointments
   - [ ] Cancel with reason capture
   - [ ] Waitlist enrollment
   - [ ] Recurring appointment setup
   - [ ] Group appointment booking
   - [ ] Telehealth appointment option

3. **Appointment Preparation:**
   - [ ] Pre-visit questionnaires
   - [ ] Document upload requirements
   - [ ] Check-in instructions
   - [ ] Parking and direction information
   - [ ] Preparation instructions
   - [ ] Reminder preferences

#### Story Points: 13
#### Priority: P0

---

### US-14.4: Secure Messaging Center
**As a** patient
**I want to** communicate securely with my care team
**So that I can** get answers to questions without office visits

#### Acceptance Criteria:
1. **Messaging Features:**
   - [ ] Compose new messages to providers
   - [ ] Reply to provider messages
   - [ ] Attach photos and documents
   - [ ] Message threading and history
   - [ ] Read receipts and timestamps
   - [ ] Priority/urgent message flagging

2. **Message Management:**
   - [ ] Inbox organization and folders
   - [ ] Search messages functionality
   - [ ] Archive and delete options
   - [ ] Print message threads
   - [ ] Auto-response for out-of-office
   - [ ] Message forwarding to care team

3. **Response Management:**
   - [ ] Expected response time display
   - [ ] Provider availability status
   - [ ] Escalation for urgent issues
   - [ ] Automated triage for common questions
   - [ ] Notification preferences
   - [ ] Message encryption indicators

#### Story Points: 13
#### Priority: P0

---

### US-14.5: Billing & Payments
**As a** patient
**I want to** view bills and make payments online
**So that I can** manage my healthcare expenses easily

#### Acceptance Criteria:
1. **Billing Display:**
   - [ ] Current balance summary
   - [ ] Detailed statement view
   - [ ] Insurance claim status
   - [ ] Payment history
   - [ ] Cost estimates for services
   - [ ] Payment plan options

2. **Payment Processing:**
   - [ ] Credit/debit card payments
   - [ ] ACH/bank transfer
   - [ ] Digital wallet integration (Apple Pay, Google Pay)
   - [ ] Saved payment methods
   - [ ] Auto-pay enrollment
   - [ ] Payment receipt generation

3. **Financial Features:**
   - [ ] Payment plan setup
   - [ ] Financial assistance applications
   - [ ] HSA/FSA integration
   - [ ] Statement download (PDF)
   - [ ] Dispute submission
   - [ ] Tax document access

#### Story Points: 13
#### Priority: P0

---

### US-14.6: Prescription Management
**As a** patient
**I want to** manage prescriptions and request refills
**So that I can** maintain medication adherence conveniently

#### Acceptance Criteria:
1. **Prescription Display:**
   - [ ] Active medication list
   - [ ] Dosage and instructions
   - [ ] Refill status and history
   - [ ] Prescription expiration alerts
   - [ ] Generic alternatives display
   - [ ] Drug interaction warnings

2. **Refill Management:**
   - [ ] One-click refill requests
   - [ ] Bulk refill requests
   - [ ] Pharmacy selection
   - [ ] Delivery options
   - [ ] Refill reminders
   - [ ] Prior authorization status

3. **Medication Tools:**
   - [ ] Medication adherence tracking
   - [ ] Pill reminder setup
   - [ ] Side effect reporting
   - [ ] Drug information library
   - [ ] Medication cost comparison
   - [ ] Prescription discount cards

#### Story Points: 8
#### Priority: P1

---

### US-14.7: Family & Proxy Access
**As a** caregiver/parent
**I want to** access family members' health information
**So that I can** help manage their healthcare needs

#### Acceptance Criteria:
1. **Access Management:**
   - [ ] Add family member accounts
   - [ ] Proxy access request/approval
   - [ ] Access level configuration
   - [ ] Minor children automatic access
   - [ ] Adult dependent management
   - [ ] Time-limited access options

2. **Account Switching:**
   - [ ] Easy account switcher
   - [ ] Clear identity indicators
   - [ ] Separate message inboxes
   - [ ] Individual notification settings
   - [ ] Activity audit trails
   - [ ] Access revocation

3. **Family Features:**
   - [ ] Family health calendar
   - [ ] Shared document storage
   - [ ] Family billing view
   - [ ] Group appointment booking
   - [ ] Emergency contact sharing
   - [ ] Care coordination tools

#### Story Points: 8
#### Priority: P1

---

## 🔨 Technical Implementation Tasks

### Frontend Development

#### Task 14.1: Portal Architecture Setup
**Description:** Establish scalable frontend architecture
**Assigned to:** Senior Frontend Engineer
**Priority:** P0
**Estimated Hours:** 40

**Sub-tasks:**
- [ ] Setup Next.js 14 with App Router
- [ ] Configure TypeScript strict mode
- [ ] Implement authentication flow
- [ ] Setup state management (Zustand)
- [ ] Configure API client (TanStack Query)
- [ ] Implement error boundaries
- [ ] Setup i18n framework
- [ ] Configure PWA capabilities
- [ ] Implement code splitting
- [ ] Setup monitoring and analytics

**Technical Requirements:**
```typescript
// Portal Application Architecture
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

// Global State Store
interface PortalState {
  user: User | null;
  patient: Patient | null;
  preferences: UserPreferences;
  notifications: Notification[];
  activeProxyAccount: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setPatient: (patient: Patient | null) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  addNotification: (notification: Notification) => void;
  switchProxyAccount: (accountId: string | null) => void;
}

export const usePortalStore = create<PortalState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        patient: null,
        preferences: {
          language: 'en',
          theme: 'light',
          notifications: {
            email: true,
            sms: true,
            push: true
          },
          accessibility: {
            fontSize: 'medium',
            highContrast: false,
            screenReader: false
          }
        },
        notifications: [],
        activeProxyAccount: null,

        setUser: (user) => set({ user }),
        setPatient: (patient) => set({ patient }),
        updatePreferences: (preferences) =>
          set((state) => ({
            preferences: { ...state.preferences, ...preferences }
          })),
        addNotification: (notification) =>
          set((state) => ({
            notifications: [...state.notifications, notification]
          })),
        switchProxyAccount: (accountId) =>
          set({ activeProxyAccount: accountId })
      }),
      {
        name: 'portal-storage',
        partialize: (state) => ({
          preferences: state.preferences,
          activeProxyAccount: state.activeProxyAccount
        })
      }
    )
  )
);

// API Client Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: 1,
      onError: (error) => {
        console.error('Mutation error:', error);
        // Global error handling
      }
    }
  }
});

// API Service Layer
class PortalAPIService {
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || '';
  }

  setAuthToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new APIError(response.status, await response.text());
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new NetworkError('Network request failed');
    }
  }

  // Patient APIs
  async getPatientProfile(): Promise<Patient> {
    return this.request<Patient>('/api/v1/patient/profile');
  }

  async updatePatientProfile(data: Partial<Patient>): Promise<Patient> {
    return this.request<Patient>('/api/v1/patient/profile', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Health Records APIs
  async getHealthRecords(filters?: RecordFilters): Promise<HealthRecord[]> {
    const params = new URLSearchParams(filters as any);
    return this.request<HealthRecord[]>(
      `/api/v1/records?${params.toString()}`
    );
  }

  async getLabResults(
    patientId: string,
    dateRange?: DateRange
  ): Promise<LabResult[]> {
    return this.request<LabResult[]>(
      `/api/v1/patients/${patientId}/lab-results`,
      {
        method: 'POST',
        body: JSON.stringify(dateRange),
      }
    );
  }

  // Appointment APIs
  async getAppointments(status?: string): Promise<Appointment[]> {
    return this.request<Appointment[]>(
      `/api/v1/appointments${status ? `?status=${status}` : ''}`
    );
  }

  async bookAppointment(data: AppointmentRequest): Promise<Appointment> {
    return this.request<Appointment>('/api/v1/appointments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async rescheduleAppointment(
    appointmentId: string,
    newDateTime: string
  ): Promise<Appointment> {
    return this.request<Appointment>(
      `/api/v1/appointments/${appointmentId}/reschedule`,
      {
        method: 'PATCH',
        body: JSON.stringify({ newDateTime }),
      }
    );
  }

  // Messaging APIs
  async getMessages(folder?: string): Promise<Message[]> {
    return this.request<Message[]>(
      `/api/v1/messages${folder ? `?folder=${folder}` : ''}`
    );
  }

  async sendMessage(message: MessageRequest): Promise<Message> {
    return this.request<Message>('/api/v1/messages', {
      method: 'POST',
      body: JSON.stringify(message),
    });
  }

  // Billing APIs
  async getBillingStatement(): Promise<BillingStatement> {
    return this.request<BillingStatement>('/api/v1/billing/statement');
  }

  async makePayment(payment: PaymentRequest): Promise<PaymentResponse> {
    return this.request<PaymentResponse>('/api/v1/billing/payment', {
      method: 'POST',
      body: JSON.stringify(payment),
    });
  }

  // Prescription APIs
  async getPrescriptions(): Promise<Prescription[]> {
    return this.request<Prescription[]>('/api/v1/prescriptions');
  }

  async requestRefill(
    prescriptionId: string,
    pharmacy?: string
  ): Promise<RefillResponse> {
    return this.request<RefillResponse>(
      `/api/v1/prescriptions/${prescriptionId}/refill`,
      {
        method: 'POST',
        body: JSON.stringify({ pharmacy }),
      }
    );
  }
}

export const portalAPI = new PortalAPIService();

// Custom Hooks
export const usePatientProfile = () => {
  return useQuery({
    queryKey: ['patient', 'profile'],
    queryFn: () => portalAPI.getPatientProfile(),
  });
};

export const useHealthRecords = (filters?: RecordFilters) => {
  return useQuery({
    queryKey: ['health-records', filters],
    queryFn: () => portalAPI.getHealthRecords(filters),
  });
};

export const useAppointments = (status?: string) => {
  return useQuery({
    queryKey: ['appointments', status],
    queryFn: () => portalAPI.getAppointments(status),
  });
};

export const useBookAppointment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AppointmentRequest) =>
      portalAPI.bookAppointment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      toast.success('Appointment booked successfully!');
    },
    onError: (error) => {
      toast.error('Failed to book appointment');
    },
  });
};

// Root Layout Component
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <ThemeProvider>
              <NotificationProvider>
                <AccessibilityProvider>
                  {children}
                </AccessibilityProvider>
              </NotificationProvider>
            </ThemeProvider>
          </AuthProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

---

#### Task 14.2: Dashboard Development
**Description:** Build comprehensive patient dashboard
**Assigned to:** Frontend Developer
**Priority:** P0
**Estimated Hours:** 32

**Sub-tasks:**
- [ ] Create dashboard layout
- [ ] Build health summary widgets
- [ ] Implement quick actions menu
- [ ] Create appointment cards
- [ ] Build medication reminders
- [ ] Implement notification center
- [ ] Create health metrics charts
- [ ] Build personalized content
- [ ] Implement dashboard customization
- [ ] Add accessibility features

**Technical Requirements:**
```typescript
// Patient Dashboard Component
import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  IconButton,
  Avatar,
  Chip,
  LinearProgress,
  Menu,
  MenuItem
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

interface DashboardProps {
  patientId: string;
}

export const PatientDashboard: React.FC<DashboardProps> = ({ patientId }) => {
  const { data: profile } = usePatientProfile();
  const { data: appointments } = useAppointments('upcoming');
  const { data: medications } = useMedications();
  const { data: healthMetrics } = useHealthMetrics();
  const { data: messages } = useUnreadMessages();

  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [dashboardLayout, setDashboardLayout] = useState(
    getDefaultLayout()
  );

  // Welcome Header
  const WelcomeHeader: React.FC = () => {
    const greeting = getTimeBasedGreeting();

    return (
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <CardContent>
          <Grid container alignItems="center">
            <Grid item xs>
              <Typography variant="h4" sx={{ color: 'white', mb: 1 }}>
                {greeting}, {profile?.firstName}!
              </Typography>
              <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                {getPersonalizedMessage(profile)}
              </Typography>
            </Grid>
            <Grid item>
              <Avatar
                src={profile?.photoUrl}
                sx={{ width: 80, height: 80 }}
              >
                {profile?.firstName?.[0]}
              </Avatar>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };

  // Health Summary Widget
  const HealthSummaryWidget: React.FC = () => {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Health Summary
          </Typography>

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Overall Health Score
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="h3" sx={{ mr: 2 }}>
                {healthMetrics?.overallScore || '--'}
              </Typography>
              <CircularProgress
                variant="determinate"
                value={healthMetrics?.overallScore || 0}
                size={60}
                thickness={4}
                sx={{
                  color: getHealthScoreColor(healthMetrics?.overallScore)
                }}
              />
            </Box>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <MetricCard
                label="Blood Pressure"
                value={healthMetrics?.bloodPressure || '--'}
                unit="mmHg"
                trend={healthMetrics?.bpTrend}
                icon={<BloodPressureIcon />}
              />
            </Grid>
            <Grid item xs={6}>
              <MetricCard
                label="Blood Sugar"
                value={healthMetrics?.bloodSugar || '--'}
                unit="mg/dL"
                trend={healthMetrics?.sugarTrend}
                icon={<GlucoseIcon />}
              />
            </Grid>
            <Grid item xs={6}>
              <MetricCard
                label="Weight"
                value={healthMetrics?.weight || '--'}
                unit="lbs"
                trend={healthMetrics?.weightTrend}
                icon={<WeightIcon />}
              />
            </Grid>
            <Grid item xs={6}>
              <MetricCard
                label="BMI"
                value={healthMetrics?.bmi || '--'}
                status={getBMIStatus(healthMetrics?.bmi)}
                icon={<BMIIcon />}
              />
            </Grid>
          </Grid>

          <Button
            fullWidth
            variant="outlined"
            sx={{ mt: 2 }}
            onClick={() => navigate('/health-records')}
          >
            View Detailed Health Records
          </Button>
        </CardContent>
      </Card>
    );
  };

  // Upcoming Appointments Widget
  const UpcomingAppointmentsWidget: React.FC = () => {
    const nextAppointment = appointments?.[0];

    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              Upcoming Appointments
            </Typography>
            <Chip
              label={`${appointments?.length || 0} scheduled`}
              size="small"
              color="primary"
            />
          </Box>

          {nextAppointment ? (
            <Box>
              <Card sx={{ bgcolor: 'primary.50', mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" color="primary">
                    NEXT APPOINTMENT
                  </Typography>
                  <Typography variant="h6">
                    {nextAppointment.providerName}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {nextAppointment.specialty}
                  </Typography>

                  <Box sx={{ mt: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <CalendarIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="body2">
                        {formatDate(nextAppointment.dateTime)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <ClockIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="body2">
                        {formatTime(nextAppointment.dateTime)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <LocationIcon sx={{ mr: 1, fontSize: 20 }} />
                      <Typography variant="body2">
                        {nextAppointment.location}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <Button size="small" variant="contained">
                      Check In
                    </Button>
                    <Button size="small" variant="outlined">
                      Reschedule
                    </Button>
                    {nextAppointment.telehealth && (
                      <Button size="small" startIcon={<VideoIcon />}>
                        Join Video
                      </Button>
                    )}
                  </Box>
                </CardContent>
              </Card>

              {appointments?.slice(1, 3).map((apt) => (
                <AppointmentListItem
                  key={apt.id}
                  appointment={apt}
                  onAction={(action) => handleAppointmentAction(apt.id, action)}
                />
              ))}
            </Box>
          ) : (
            <EmptyState
              icon={<CalendarIcon />}
              message="No upcoming appointments"
              action={
                <Button variant="contained" fullWidth>
                  Schedule Appointment
                </Button>
              }
            />
          )}

          {appointments && appointments.length > 3 && (
            <Button
              fullWidth
              sx={{ mt: 2 }}
              onClick={() => navigate('/appointments')}
            >
              View All Appointments ({appointments.length})
            </Button>
          )}
        </CardContent>
      </Card>
    );
  };

  // Medication Reminders Widget
  const MedicationRemindersWidget: React.FC = () => {
    const todaysMeds = medications?.filter(m => m.nextDose === 'today');

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Medication Reminders
          </Typography>

          {todaysMeds?.map((medication) => (
            <Box
              key={medication.id}
              sx={{
                p: 2,
                mb: 1,
                bgcolor: medication.taken ? 'success.50' : 'warning.50',
                borderRadius: 1
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="subtitle1">
                    {medication.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {medication.dosage} • {medication.frequency}
                  </Typography>
                  <Typography variant="caption">
                    Next dose: {formatTime(medication.nextDoseTime)}
                  </Typography>
                </Box>
                <Box>
                  {medication.taken ? (
                    <Chip
                      label="Taken"
                      color="success"
                      icon={<CheckCircleIcon />}
                    />
                  ) : (
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => markMedicationTaken(medication.id)}
                    >
                      Mark as Taken
                    </Button>
                  )}
                </Box>
              </Box>

              {medication.refillsRemaining <= 1 && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  {medication.refillsRemaining === 0
                    ? 'No refills remaining'
                    : 'Last refill available'}
                  <Button size="small" sx={{ ml: 1 }}>
                    Request Refill
                  </Button>
                </Alert>
              )}
            </Box>
          ))}

          <Button
            fullWidth
            variant="outlined"
            sx={{ mt: 2 }}
            onClick={() => navigate('/prescriptions')}
          >
            Manage All Medications
          </Button>
        </CardContent>
      </Card>
    );
  };

  // Health Metrics Chart
  const HealthMetricsChart: React.FC = () => {
    const [selectedMetric, setSelectedMetric] = useState('bloodPressure');
    const [timeRange, setTimeRange] = useState('30d');

    const chartData = {
      labels: getChartLabels(timeRange),
      datasets: [
        {
          label: getMetricLabel(selectedMetric),
          data: healthMetrics?.[selectedMetric]?.history || [],
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.4
        }
      ]
    };

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    };

    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              Health Trends
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                size="small"
              >
                <MenuItem value="bloodPressure">Blood Pressure</MenuItem>
                <MenuItem value="bloodSugar">Blood Sugar</MenuItem>
                <MenuItem value="weight">Weight</MenuItem>
                <MenuItem value="heartRate">Heart Rate</MenuItem>
              </Select>
              <ToggleButtonGroup
                value={timeRange}
                exclusive
                onChange={(e, value) => setTimeRange(value)}
                size="small"
              >
                <ToggleButton value="7d">7D</ToggleButton>
                <ToggleButton value="30d">30D</ToggleButton>
                <ToggleButton value="90d">90D</ToggleButton>
                <ToggleButton value="1y">1Y</ToggleButton>
              </ToggleButtonGroup>
            </Box>
          </Box>

          <Box sx={{ height: 300 }}>
            <Line data={chartData} options={chartOptions} />
          </Box>

          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Insights
            </Typography>
            <Typography variant="body2">
              {getMetricInsight(selectedMetric, healthMetrics)}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  // Quick Actions
  const QuickActionsWidget: React.FC = () => {
    const quickActions = [
      {
        icon: <CalendarIcon />,
        label: 'Book Appointment',
        action: '/appointments/new',
        color: 'primary'
      },
      {
        icon: <MessageIcon />,
        label: 'Message Provider',
        action: '/messages/compose',
        color: 'secondary'
      },
      {
        icon: <RefillIcon />,
        label: 'Request Refill',
        action: '/prescriptions/refill',
        color: 'success'
      },
      {
        icon: <PaymentIcon />,
        label: 'Pay Bill',
        action: '/billing/payment',
        color: 'warning'
      },
      {
        icon: <DocumentIcon />,
        label: 'View Records',
        action: '/health-records',
        color: 'info'
      },
      {
        icon: <VideoIcon />,
        label: 'Telehealth Visit',
        action: '/telehealth',
        color: 'error'
      }
    ];

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>

          <Grid container spacing={2}>
            {quickActions.map((action) => (
              <Grid item xs={4} key={action.label}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Card
                    sx={{
                      p: 2,
                      textAlign: 'center',
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: `${action.color}.50`
                      }
                    }}
                    onClick={() => navigate(action.action)}
                  >
                    <Avatar
                      sx={{
                        bgcolor: `${action.color}.main`,
                        width: 48,
                        height: 48,
                        margin: '0 auto',
                        mb: 1
                      }}
                    >
                      {action.icon}
                    </Avatar>
                    <Typography variant="caption">
                      {action.label}
                    </Typography>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <WelcomeHeader />

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <HealthSummaryWidget />
            </Grid>
            <Grid item xs={12}>
              <HealthMetricsChart />
            </Grid>
            <Grid item xs={12}>
              <MedicationRemindersWidget />
            </Grid>
          </Grid>
        </Grid>

        <Grid item xs={12} md={4}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <UpcomingAppointmentsWidget />
            </Grid>
            <Grid item xs={12}>
              <QuickActionsWidget />
            </Grid>
            <Grid item xs={12}>
              <RecentMessagesWidget />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};
```

---

#### Task 14.3: Health Records Interface
**Description:** Build comprehensive health records viewer
**Assigned to:** Frontend Developer
**Priority:** P0
**Estimated Hours:** 32

**Sub-tasks:**
- [ ] Create records navigation
- [ ] Build lab results viewer
- [ ] Implement imaging viewer
- [ ] Create visit summaries
- [ ] Build medication history
- [ ] Implement immunization records
- [ ] Create document viewer
- [ ] Build export functionality
- [ ] Implement sharing features
- [ ] Add print layouts

---

#### Task 14.4: Appointment Management UI
**Description:** Build appointment booking and management interface
**Assigned to:** Frontend Developer
**Priority:** P0
**Estimated Hours:** 32

**Sub-tasks:**
- [ ] Create appointment calendar
- [ ] Build provider selection
- [ ] Implement slot selection
- [ ] Create booking confirmation
- [ ] Build reschedule interface
- [ ] Implement cancellation flow
- [ ] Create waitlist management
- [ ] Build reminder preferences
- [ ] Implement check-in process
- [ ] Add telehealth integration

---

### Backend Development

#### Task 14.5: Portal API Development
**Description:** Build comprehensive portal backend APIs
**Assigned to:** Senior Backend Engineer
**Priority:** P0
**Estimated Hours:** 40

**Sub-tasks:**
- [ ] Design API architecture
- [ ] Implement authentication system
- [ ] Build patient profile APIs
- [ ] Create health records APIs
- [ ] Implement appointment APIs
- [ ] Build messaging APIs
- [ ] Create billing APIs
- [ ] Implement prescription APIs
- [ ] Build notification system
- [ ] Setup API documentation

**Technical Requirements:**
```python
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import jwt
from passlib.context import CryptContext
import asyncpg
from redis import Redis
import boto3

app = FastAPI(title="Patient Portal API", version="1.0.0")

# Security Configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=7)

    async def authenticate_patient(
        self,
        email: str,
        password: str,
        mfa_code: Optional[str] = None
    ) -> Dict:
        """Authenticate patient with optional MFA"""

        # Verify credentials
        patient = await self.get_patient_by_email(email)
        if not patient or not self.verify_password(password, patient['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check MFA if enabled
        if patient['mfa_enabled']:
            if not mfa_code or not self.verify_mfa(patient['id'], mfa_code):
                return {
                    'requires_mfa': True,
                    'patient_id': patient['id']
                }

        # Generate tokens
        access_token = self.create_access_token(patient['id'])
        refresh_token = self.create_refresh_token(patient['id'])

        # Log successful login
        await self.log_login_event(patient['id'])

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'patient': self.sanitize_patient(patient)
        }

    def create_access_token(self, patient_id: str) -> str:
        """Create JWT access token"""
        payload = {
            'sub': patient_id,
            'type': 'access',
            'exp': datetime.utcnow() + self.access_token_expire,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> str:
        """Verify JWT token and return patient ID"""
        token = credentials.credentials

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            if payload['type'] != 'access':
                raise HTTPException(status_code=401, detail="Invalid token type")

            # Check if token is blacklisted
            if await self.is_token_blacklisted(token):
                raise HTTPException(status_code=401, detail="Token has been revoked")

            return payload['sub']

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# Patient Profile Service
class PatientService:
    def __init__(self):
        self.db_pool = None
        self.cache = Redis()

    async def get_patient_profile(self, patient_id: str) -> Dict:
        """Get complete patient profile"""

        # Check cache first
        cached = self.cache.get(f"patient:{patient_id}")
        if cached:
            return json.loads(cached)

        query = """
        SELECT
            p.id,
            p.mrn,
            p.first_name,
            p.last_name,
            p.date_of_birth,
            p.gender,
            p.email,
            p.phone,
            p.address,
            p.emergency_contacts,
            p.insurance_info,
            p.preferred_language,
            p.photo_url,
            p.created_at,
            p.updated_at,

            -- Aggregate related data
            COUNT(DISTINCT a.id) as total_appointments,
            COUNT(DISTINCT m.id) as active_medications,
            COUNT(DISTINCT al.id) as active_allergies,
            MAX(v.visit_date) as last_visit_date

        FROM patients p
        LEFT JOIN appointments a ON p.id = a.patient_id
        LEFT JOIN medications m ON p.id = m.patient_id AND m.active = true
        LEFT JOIN allergies al ON p.id = al.patient_id
        LEFT JOIN visits v ON p.id = v.patient_id

        WHERE p.id = $1
        GROUP BY p.id
        """

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, patient_id)

            if not row:
                raise HTTPException(status_code=404, detail="Patient not found")

            profile = dict(row)

            # Get additional details
            profile['health_summary'] = await self.get_health_summary(patient_id)
            profile['care_team'] = await self.get_care_team(patient_id)
            profile['preferences'] = await self.get_patient_preferences(patient_id)

            # Cache for 5 minutes
            self.cache.setex(
                f"patient:{patient_id}",
                300,
                json.dumps(profile, default=str)
            )

            return profile

    async def update_patient_profile(
        self,
        patient_id: str,
        updates: Dict
    ) -> Dict:
        """Update patient profile information"""

        allowed_fields = [
            'phone', 'email', 'address', 'emergency_contacts',
            'preferred_language', 'communication_preferences'
        ]

        # Filter to allowed fields only
        filtered_updates = {
            k: v for k, v in updates.items()
            if k in allowed_fields
        }

        if not filtered_updates:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )

        # Build update query
        set_clauses = [f"{k} = ${i+2}" for i, k in enumerate(filtered_updates.keys())]
        query = f"""
        UPDATE patients
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                patient_id,
                *filtered_updates.values()
            )

            # Clear cache
            self.cache.delete(f"patient:{patient_id}")

            # Log profile update
            await self.audit_log(
                patient_id,
                'profile_update',
                filtered_updates
            )

            return dict(row)

# Health Records Service
class HealthRecordsService:
    async def get_health_records(
        self,
        patient_id: str,
        record_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict]:
        """Get patient health records with filtering"""

        base_query = """
        SELECT
            r.id,
            r.record_type,
            r.encounter_id,
            r.provider_name,
            r.record_date,
            r.title,
            r.content,
            r.attachments,
            r.is_sensitive,
            r.created_at,
            e.visit_type,
            e.facility_name

        FROM health_records r
        LEFT JOIN encounters e ON r.encounter_id = e.id
        WHERE r.patient_id = $1
        """

        params = [patient_id]
        param_count = 1

        if record_type:
            param_count += 1
            base_query += f" AND r.record_type = ${param_count}"
            params.append(record_type)

        if date_from:
            param_count += 1
            base_query += f" AND r.record_date >= ${param_count}"
            params.append(date_from)

        if date_to:
            param_count += 1
            base_query += f" AND r.record_date <= ${param_count}"
            params.append(date_to)

        base_query += " ORDER BY r.record_date DESC"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)

            records = []
            for row in rows:
                record = dict(row)

                # Check access permissions
                if record['is_sensitive'] and not await self.check_sensitive_access(
                    patient_id
                ):
                    record['content'] = "[Restricted - Contact provider for access]"

                records.append(record)

            # Log access
            await self.audit_log(
                patient_id,
                'records_accessed',
                {'count': len(records), 'type': record_type}
            )

            return records

    async def get_lab_results(
        self,
        patient_id: str,
        test_type: Optional[str] = None
    ) -> List[Dict]:
        """Get lab results with trending"""

        query = """
        SELECT
            lr.id,
            lr.test_name,
            lr.test_code,
            lr.result_value,
            lr.result_unit,
            lr.reference_range,
            lr.abnormal_flag,
            lr.result_date,
            lr.ordering_provider,
            lr.performing_lab,
            lr.status,
            lr.comments,

            -- Get previous result for trending
            LAG(lr.result_value) OVER (
                PARTITION BY lr.test_code
                ORDER BY lr.result_date
            ) as previous_value,

            LAG(lr.result_date) OVER (
                PARTITION BY lr.test_code
                ORDER BY lr.result_date
            ) as previous_date

        FROM lab_results lr
        WHERE lr.patient_id = $1
        """

        params = [patient_id]

        if test_type:
            query += " AND lr.test_category = $2"
            params.append(test_type)

        query += " ORDER BY lr.result_date DESC"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                result = dict(row)

                # Calculate trend
                if result['previous_value']:
                    result['trend'] = self.calculate_trend(
                        result['result_value'],
                        result['previous_value']
                    )

                # Parse reference range
                result['in_range'] = self.check_in_range(
                    result['result_value'],
                    result['reference_range']
                )

                results.append(result)

            return results

# Appointment Service
class AppointmentService:
    async def get_available_slots(
        self,
        provider_id: Optional[str],
        specialty: Optional[str],
        date_from: datetime,
        date_to: datetime,
        appointment_type: str
    ) -> List[Dict]:
        """Get available appointment slots"""

        # Get provider schedules
        providers = await self.get_providers(provider_id, specialty)

        available_slots = []

        for provider in providers:
            # Get provider's schedule template
            schedule = await self.get_provider_schedule(provider['id'])

            # Get existing appointments
            existing = await self.get_existing_appointments(
                provider['id'],
                date_from,
                date_to
            )

            # Generate available slots
            slots = self.generate_slots(
                schedule,
                existing,
                date_from,
                date_to,
                appointment_type
            )

            for slot in slots:
                available_slots.append({
                    'provider_id': provider['id'],
                    'provider_name': provider['name'],
                    'specialty': provider['specialty'],
                    'datetime': slot['datetime'],
                    'duration': slot['duration'],
                    'location': provider['location'],
                    'telehealth_available': provider['telehealth_enabled'],
                    'new_patient_available': slot['new_patient']
                })

        # Sort by datetime
        available_slots.sort(key=lambda x: x['datetime'])

        return available_slots

    async def book_appointment(
        self,
        patient_id: str,
        appointment_data: Dict
    ) -> Dict:
        """Book a new appointment"""

        # Validate slot availability
        if not await self.is_slot_available(
            appointment_data['provider_id'],
            appointment_data['datetime']
        ):
            raise HTTPException(
                status_code=400,
                detail="Selected time slot is no longer available"
            )

        # Check for conflicts
        if await self.has_conflict(patient_id, appointment_data['datetime']):
            raise HTTPException(
                status_code=400,
                detail="You have another appointment at this time"
            )

        # Create appointment
        query = """
        INSERT INTO appointments (
            patient_id,
            provider_id,
            appointment_datetime,
            appointment_type,
            duration_minutes,
            location,
            reason_for_visit,
            telehealth,
            status,
            created_by,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
        RETURNING *
        """

        async with self.db_pool.acquire() as conn:
            appointment = await conn.fetchrow(
                query,
                patient_id,
                appointment_data['provider_id'],
                appointment_data['datetime'],
                appointment_data['appointment_type'],
                appointment_data.get('duration', 30),
                appointment_data.get('location'),
                appointment_data.get('reason'),
                appointment_data.get('telehealth', False),
                'scheduled',
                patient_id
            )

            appointment = dict(appointment)

            # Send confirmation
            await self.send_appointment_confirmation(appointment)

            # Schedule reminders
            await self.schedule_reminders(appointment)

            return appointment

# Messaging Service
class MessagingService:
    async def send_secure_message(
        self,
        patient_id: str,
        message_data: Dict
    ) -> Dict:
        """Send secure message to provider"""

        # Validate recipient
        if not await self.validate_recipient(
            patient_id,
            message_data['recipient_id']
        ):
            raise HTTPException(
                status_code=403,
                detail="You can only message your care team"
            )

        # Check for PHI and encrypt if needed
        encrypted_content = await self.encrypt_if_needed(
            message_data['content']
        )

        query = """
        INSERT INTO secure_messages (
            sender_id,
            sender_type,
            recipient_id,
            recipient_type,
            subject,
            content,
            encrypted,
            attachments,
            priority,
            thread_id,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
        RETURNING *
        """

        async with self.db_pool.acquire() as conn:
            message = await conn.fetchrow(
                query,
                patient_id,
                'patient',
                message_data['recipient_id'],
                'provider',
                message_data.get('subject', ''),
                encrypted_content,
                message_data.get('content') != encrypted_content,
                message_data.get('attachments', []),
                message_data.get('priority', 'normal'),
                message_data.get('thread_id')
            )

            # Send notification to recipient
            await self.notify_recipient(message)

            return dict(message)

    async def get_messages(
        self,
        patient_id: str,
        folder: str = 'inbox'
    ) -> List[Dict]:
        """Get patient messages"""

        if folder == 'inbox':
            condition = "recipient_id = $1 AND recipient_type = 'patient'"
        elif folder == 'sent':
            condition = "sender_id = $1 AND sender_type = 'patient'"
        else:
            condition = "(recipient_id = $1 AND recipient_type = 'patient') OR (sender_id = $1 AND sender_type = 'patient')"

        query = f"""
        SELECT
            m.*,
            CASE
                WHEN m.sender_type = 'provider' THEN p.full_name
                WHEN m.sender_type = 'patient' THEN pt.full_name
            END as sender_name,
            CASE
                WHEN m.recipient_type = 'provider' THEN p2.full_name
                WHEN m.recipient_type = 'patient' THEN pt2.full_name
            END as recipient_name

        FROM secure_messages m
        LEFT JOIN providers p ON m.sender_id = p.id AND m.sender_type = 'provider'
        LEFT JOIN patients pt ON m.sender_id = pt.id AND m.sender_type = 'patient'
        LEFT JOIN providers p2 ON m.recipient_id = p2.id AND m.recipient_type = 'provider'
        LEFT JOIN patients pt2 ON m.recipient_id = pt2.id AND m.recipient_type = 'patient'

        WHERE {condition}
        ORDER BY m.created_at DESC
        """

        async with self.db_pool.acquire() as conn:
            messages = await conn.fetch(query, patient_id)

            return [dict(m) for m in messages]
```

---

#### Task 14.6: Security & Authentication
**Description:** Implement comprehensive security system
**Assigned to:** Security Engineer
**Priority:** P0
**Estimated Hours:** 32

**Sub-tasks:**
- [ ] Implement OAuth 2.0/OIDC
- [ ] Build MFA system
- [ ] Create session management
- [ ] Implement RBAC
- [ ] Build audit logging
- [ ] Setup encryption
- [ ] Implement rate limiting
- [ ] Create security headers
- [ ] Build CSRF protection
- [ ] Implement account lockout

---

#### Task 14.7: Payment Processing
**Description:** Build secure payment system
**Assigned to:** Backend Engineer
**Priority:** P0
**Estimated Hours:** 32

**Sub-tasks:**
- [ ] Integrate Stripe/Square
- [ ] Build payment forms
- [ ] Implement PCI compliance
- [ ] Create payment plans
- [ ] Build refund system
- [ ] Implement receipts
- [ ] Create payment history
- [ ] Build HSA/FSA integration
- [ ] Implement auto-pay
- [ ] Create payment analytics

---

### Mobile Optimization

#### Task 14.8: Progressive Web App
**Description:** Build PWA capabilities
**Assigned to:** Frontend Developer
**Priority:** P1
**Estimated Hours:** 24

**Sub-tasks:**
- [ ] Setup service worker
- [ ] Implement offline support
- [ ] Build app manifest
- [ ] Create push notifications
- [ ] Implement background sync
- [ ] Build install prompts
- [ ] Create app icons
- [ ] Implement deep linking
- [ ] Build splash screens
- [ ] Setup cache strategies

---

#### Task 14.9: Responsive Design
**Description:** Ensure mobile-first responsive design
**Assigned to:** UI/UX Developer
**Priority:** P0
**Estimated Hours:** 24

**Sub-tasks:**
- [ ] Create responsive layouts
- [ ] Build touch-optimized controls
- [ ] Implement gesture support
- [ ] Create mobile navigation
- [ ] Build adaptive components
- [ ] Optimize images
- [ ] Implement lazy loading
- [ ] Create mobile-specific views
- [ ] Build orientation handling
- [ ] Test on all devices

---

### Integration & Data

#### Task 14.10: EHR Integration
**Description:** Build EHR data synchronization
**Assigned to:** Integration Engineer
**Priority:** P0
**Estimated Hours:** 40

**Sub-tasks:**
- [ ] Setup FHIR client
- [ ] Build data mapping
- [ ] Implement sync jobs
- [ ] Create conflict resolution
- [ ] Build error handling
- [ ] Implement retry logic
- [ ] Setup monitoring
- [ ] Create data validation
- [ ] Build audit trail
- [ ] Implement rollback

---

#### Task 14.11: Third-party Integrations
**Description:** Integrate external services
**Assigned to:** Backend Engineer
**Priority:** P1
**Estimated Hours:** 32

**Sub-tasks:**
- [ ] Pharmacy integration
- [ ] Lab system connection
- [ ] Insurance verification
- [ ] Telehealth platform
- [ ] Wearables integration
- [ ] Document signing
- [ ] Survey tools
- [ ] Education content
- [ ] Transportation services
- [ ] Language translation

---

### Analytics & Monitoring

#### Task 14.12: Portal Analytics
**Description:** Build usage analytics system
**Assigned to:** Data Engineer
**Priority:** P1
**Estimated Hours:** 24

**Sub-tasks:**
- [ ] Implement event tracking
- [ ] Build user journey tracking
- [ ] Create engagement metrics
- [ ] Implement A/B testing
- [ ] Build conversion tracking
- [ ] Create heatmaps
- [ ] Implement session recording
- [ ] Build performance metrics
- [ ] Create custom reports
- [ ] Setup alerting

---

#### Task 14.13: Performance Optimization
**Description:** Optimize portal performance
**Assigned to:** Performance Engineer
**Priority:** P1
**Estimated Hours:** 24

**Sub-tasks:**
- [ ] Implement CDN
- [ ] Setup caching layers
- [ ] Optimize database queries
- [ ] Build lazy loading
- [ ] Implement code splitting
- [ ] Optimize bundle size
- [ ] Setup compression
- [ ] Implement prefetching
- [ ] Build performance monitoring
- [ ] Create performance budget

---

## 📐 Technical Architecture

### System Architecture
```yaml
patient_portal:
  frontend:
    framework: "Next.js 14 with App Router"
    styling: "Tailwind CSS + Material UI"
    state: "Zustand"
    data_fetching: "TanStack Query"
    forms: "React Hook Form + Zod"

  backend:
    api: "FastAPI"
    database: "PostgreSQL"
    cache: "Redis"
    queue: "BullMQ"
    storage: "S3"

  authentication:
    provider: "Auth0 / Custom JWT"
    mfa: "TOTP / SMS"
    sso: "SAML 2.0"

  integrations:
    ehr: "FHIR R4 APIs"
    payments: "Stripe"
    communications: "Twilio"
    analytics: "Mixpanel"
    monitoring: "Datadog"

  security:
    encryption: "AES-256"
    certificates: "TLS 1.3"
    headers: "HSTS, CSP, X-Frame-Options"
    audit: "Comprehensive logging"
```

### Data Model
```sql
-- Core Patient Portal Tables

CREATE TABLE portal_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    mfa_secret VARCHAR(255),
    mfa_enabled BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portal_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES portal_users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE proxy_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grantor_id UUID REFERENCES patients(id),
    grantee_id UUID REFERENCES portal_users(id),
    relationship VARCHAR(50),
    access_level VARCHAR(50),
    permissions JSONB,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE secure_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID,
    sender_id UUID NOT NULL,
    sender_type VARCHAR(20),
    recipient_id UUID NOT NULL,
    recipient_type VARCHAR(20),
    subject VARCHAR(255),
    content TEXT,
    encrypted BOOLEAN DEFAULT false,
    attachments JSONB,
    priority VARCHAR(20) DEFAULT 'normal',
    read_at TIMESTAMP,
    replied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portal_preferences (
    user_id UUID PRIMARY KEY REFERENCES portal_users(id),
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    theme VARCHAR(20) DEFAULT 'light',
    notifications JSONB,
    dashboard_layout JSONB,
    accessibility JSONB,
    communication_preferences JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portal_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES portal_users(id),
    patient_id UUID REFERENCES patients(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_portal_users_email ON portal_users(email);
CREATE INDEX idx_portal_sessions_user ON portal_sessions(user_id);
CREATE INDEX idx_proxy_access_grantee ON proxy_access(grantee_id);
CREATE INDEX idx_messages_recipient ON secure_messages(recipient_id, recipient_type);
CREATE INDEX idx_audit_log_user ON portal_audit_log(user_id, created_at DESC);
```

---

## 🔒 Security Considerations

### Security Requirements
1. **Authentication:**
   - Multi-factor authentication
   - Biometric login support
   - Account lockout policies
   - Password complexity requirements

2. **Authorization:**
   - Role-based access control
   - Proxy access management
   - Resource-level permissions
   - Time-based access

3. **Data Protection:**
   - End-to-end encryption for messages
   - At-rest encryption for PHI
   - Secure file upload/download
   - Data masking for sensitive info

4. **Compliance:**
   - HIPAA compliance
   - WCAG 2.1 AA accessibility
   - State privacy laws
   - Audit trail requirements

---

## 🧪 Testing Strategy

### Testing Approach
1. **Unit Testing:**
   - Component testing with RTL
   - API endpoint testing
   - Service layer testing
   - Utility function testing

2. **Integration Testing:**
   - E2E user workflows
   - API integration tests
   - Database transaction tests
   - Third-party service mocks

3. **Performance Testing:**
   - Load testing with k6
   - Stress testing
   - Database performance
   - CDN effectiveness

4. **Security Testing:**
   - Penetration testing
   - OWASP compliance
   - Authentication testing
   - Authorization verification

---

## 📋 Rollout Plan

### Phase 1: Core Features (Week 1)
- User registration and authentication
- Basic health records viewing
- Appointment display
- Simple messaging

### Phase 2: Interactive Features (Week 2)
- Appointment booking
- Prescription refills
- Bill payment
- Full messaging

### Phase 3: Advanced Features (Week 3)
- Proxy access
- Mobile app features
- Advanced dashboards
- Integrations

### Phase 4: Optimization (Week 4)
- Performance tuning
- Analytics implementation
- A/B testing
- Full production launch

---

## 📊 Success Metrics

### Week 1 Targets
- Portal framework complete
- 5 core features functional
- Authentication working
- Basic UI complete

### Month 1 Targets
- 1000 registered users
- 75% adoption rate
- 50% self-service rate
- 4.0+ satisfaction score

### Quarter 1 Targets
- 10,000 active users
- 60% call reduction
- 80% online appointments
- 95% satisfaction rate

---

## 🔗 Dependencies

### Technical Dependencies
- EPIC-001: Real-time messaging
- EPIC-005: FHIR integration
- EPIC-013: Omnichannel communications
- EPIC-016: Mobile applications

### External Dependencies
- EHR system APIs
- Payment processor accounts
- SMS/Email providers
- Identity verification service

### Resource Dependencies
- 2 Frontend Developers
- 2 Backend Engineers
- 1 UI/UX Designer
- 1 Security Engineer

---

## 📝 Notes

### Key Decisions
- Chose Next.js 14 for performance and SEO
- Implemented PWA for mobile experience
- Built comprehensive proxy access system
- Prioritized accessibility compliance

### Risks & Mitigations
- **Risk:** Low adoption rates
  - **Mitigation:** Intuitive UX and onboarding support

- **Risk:** Security breaches
  - **Mitigation:** Multi-layer security and regular audits

- **Risk:** Performance issues at scale
  - **Mitigation:** Caching, CDN, and database optimization

---

**Epic Status:** Ready for Implementation
**Last Updated:** November 24, 2024
**Next Review:** Sprint Planning