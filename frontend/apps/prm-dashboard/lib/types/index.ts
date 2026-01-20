// ==================== Common Types ====================

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'doctor' | 'nurse' | 'receptionist' | 'care_coordinator';
  org_id: string;
  permissions: string[];
}

export interface Organization {
  id: string;
  name: string;
  type: string;
  settings: Record<string, any>;
}

// ==================== Patient Types ====================

export interface Patient {
  id: string;
  mrn: string;
  name: string;
  /** Backend uses legal_name instead of name */
  legal_name?: string;
  phone: string;
  /** Backend uses primary_phone instead of phone */
  primary_phone?: string;
  email?: string;
  date_of_birth: string;
  gender: 'male' | 'female' | 'other';
  blood_group?: string;
  address?: string;
  emergency_contact?: {
    name: string;
    phone: string;
    relationship: string;
  };
  /** Patient status for dashboard display */
  status?: 'active' | 'inactive' | 'pending';
  /** Avatar URL for profile display */
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

// ==================== Appointment Types ====================

export interface Practitioner {
  id: string;
  name: string;
  speciality: string;
  qualification: string;
  phone?: string;
  email?: string;
}

export interface AppointmentSlot {
  id: string;
  practitioner_id: string;
  start_time: string;
  end_time: string;
  duration: number;
  status: 'available' | 'booked' | 'blocked';
  location: Location;
}

export interface Appointment {
  id: string;
  patient_id: string;
  patient: Patient;
  practitioner_id: string;
  practitioner: Practitioner;
  start_time: string;
  scheduled_at?: string; // Mapped from start_time for frontend compatibility
  end_time: string;
  /** Alias for start_time used in some views */
  scheduled_at?: string;
  appointment_type: 'consultation' | 'follow_up' | 'procedure' | 'test';
  status: 'scheduled' | 'confirmed' | 'checked_in' | 'completed' | 'cancelled' | 'no_show';
  notes?: string;
  location: Location;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: string;
  name: string;
  address?: string;
  room?: string;
}

// ==================== Journey Types ====================

export interface JourneyStage {
  id: string;
  name: string;
  description?: string;
  sequence: number;
  actions: JourneyAction[];
}

export interface JourneyAction {
  type: 'send_communication' | 'create_task' | 'wait' | 'condition';
  config: Record<string, any>;
}

export interface JourneyDefinition {
  id: string;
  name: string;
  description?: string;
  journey_type: string;
  stages: JourneyStage[];
  is_active: boolean;
  is_default: boolean;
  org_id: string;
  created_at: string;
  updated_at: string;
}

export interface JourneyInstance {
  id: string;
  journey_id: string;
  journey: JourneyDefinition;
  patient_id: string;
  patient: Patient;
  current_stage: number;
  status: 'active' | 'paused' | 'completed' | 'cancelled';
  context: Record<string, any>;
  started_at: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

/** Journey type used by the journeys page */
export interface Journey {
  id: string;
  title?: string;
  description?: string;
  journey_type?: string;
  patient_id?: string;
  patient?: Patient;
  status: 'active' | 'paused' | 'completed' | 'cancelled';
  current_stage?: number;
  steps?: JourneyStep[];
  context?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface JourneyStep {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  completed_at?: string;
}

// ==================== Communication Types ====================

export interface Communication {
  id: string;
  patient_id: string;
  patient: Patient;
  channel: 'whatsapp' | 'sms' | 'email' | 'voice';
  direction: 'inbound' | 'outbound';
  content: string;
  /** @deprecated Use `content` instead. Kept for backward compatibility. */
  message?: string;
  /** Email subject line */
  subject?: string;
  /** @deprecated Use `content` instead. Kept for backward compatibility. */
  body?: string;
  status: 'queued' | 'sent' | 'delivered' | 'read' | 'failed' | 'pending';
  media_url?: string;
  template_id?: string;
  sent_by?: string;
  sent_at: string;
  delivered_at?: string;
  read_at?: string;
  error_message?: string;
  created_at: string;
}

export interface CommunicationTemplate {
  id: string;
  name: string;
  category: string;
  channel: 'whatsapp' | 'sms' | 'email';
  content: string;
  variables: string[];
  org_id: string;
}

// ==================== Ticket Types ====================

export interface Ticket {
  id: string;
  title: string;
  description: string;
  patient_id?: string;
  patient?: Patient;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  category: string;
  assigned_to?: string;
  linked_journey_id?: string;
  linked_appointment_id?: string;
  resolution_notes?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}

// ==================== API Types ====================

export interface APIResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface APIError {
  code: string;
  message: string;
  details?: any;
}
