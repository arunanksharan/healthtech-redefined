export interface Tenant {
    id: string;
    name: string;
}

export interface Pagination {
    page: number;
    page_size: number;
    total: number;
    has_next: boolean;
    has_previous: boolean;
}

// ==================== Journeys ====================

export interface Journey {
    id: string;
    tenant_id: string;
    name: string;
    description?: string;
    journey_type: 'opd' | 'ipd' | 'procedure' | 'chronic_care' | 'wellness';
    is_default: boolean;
    trigger_conditions?: Record<string, any>;
    stages: JourneyStage[];
    created_at: string;
    updated_at: string;
}

export interface JourneyStage {
    id: string;
    journey_id: string;
    name: string;
    description?: string;
    order_index: number;
    trigger_event?: string;
    actions?: Record<string, any>;
    created_at: string;
    updated_at: string;
}

export interface JourneyInstance {
    id: string;
    tenant_id: string;
    journey_id: string;
    patient_id: string;
    appointment_id?: string;
    encounter_id?: string;
    status: string; // active, completed, cancelled
    current_stage_id?: string;
    context?: Record<string, any>;
    started_at: string;
    completed_at?: string;
    created_at: string;
    updated_at: string;
    // Expanded fields commonly needed for UI
    patient?: { name: string; id: string;[key: string]: any };
    journey?: { name: string; title?: string;[key: string]: any };
}

export interface JourneyInstanceWithStages extends JourneyInstance {
    journey_name: string;
    stages: Record<string, any>[]; // Expanded stage status
}

// ==================== Communications ====================

export type CommunicationChannel = 'whatsapp' | 'sms' | 'email' | 'voice' | 'in_app';

export interface Communication {
    id: string;
    tenant_id: string;
    patient_id: string;
    journey_instance_id?: string;
    channel: CommunicationChannel;
    recipient: string;
    subject?: string;
    message: string;
    template_name?: string;
    status: string; // sent, delivered, failed, read
    scheduled_for?: string;
    sent_at?: string;
    delivered_at?: string;
    read_at?: string;
    error_message?: string;
    created_at: string;
    updated_at: string;
}

// ==================== Tickets ====================

export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Ticket {
    id: string;
    tenant_id: string;
    patient_id: string;
    journey_instance_id?: string;
    title: string;
    description: string;
    status: TicketStatus;
    priority: TicketPriority;
    category?: string;
    assigned_to?: string;
    resolution_notes?: string;
    resolved_at?: string;
    created_at: string;
    updated_at: string;
    comments?: TicketComment[];
}

export interface TicketComment {
    id: string;
    ticket_id: string;
    user_id: string;
    comment: string;
    is_internal: boolean;
    created_at: string;
}

// ==================== API Responses ====================

export interface JourneyListResponse {
    total: number;
    journeys: Journey[];
    page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
}

export interface JourneyInstanceStats {
    total: number;
    active: number;
    completed: number;
    cancelled: number;
    by_status: Record<string, number>;
    by_journey: Record<string, number>;
}

export interface JourneyInstanceListResponse {
    total: number;
    instances: JourneyInstance[];
    page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
}

export interface CommunicationListResponse {
    total: number;
    communications: Communication[];
    page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
}

export interface TicketListResponse {
    total: number;
    tickets: Ticket[];
    page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
}

export interface CommunicationStats {
    total: number;
    by_channel: Record<string, number>;
    by_status: Record<string, number>;
}

// ==================== Patient 360 View ====================

export interface Patient360Appointment {
    id: string;
    scheduled_at: string | null;
    status: string;
    appointment_type: string;
    practitioner_id: string | null;
}

export interface Patient360Journey {
    id: string;
    journey_id: string;
    status: string;
    current_stage_id: string | null;
}

export interface Patient360Ticket {
    id: string;
    title: string;
    status: string;
    priority: string;
}

export interface Patient360Communication {
    id: string;
    channel: string;
    direction: string;
    sent_at: string | null;
    message_type: string;
}

export interface PatientSimple {
    id: string;
    mrn?: string;
    first_name: string;
    last_name: string;
    legal_name?: string;
    date_of_birth: string;
    gender: string;
    phone_primary?: string;
    email_primary?: string;
    is_deceased?: boolean;
    state?: string; // active, inactive
    created_at: string;
}

export interface Patient360Response {
    patient: PatientSimple;
    appointments: Patient360Appointment[];
    journeys: Patient360Journey[];
    tickets: Patient360Ticket[];
    communications: Patient360Communication[];
    total_appointments: number;
    upcoming_appointments: number;
    active_journeys: number;
    open_tickets: number;
    recent_communications: number;
    last_visit_date: string | null;
    next_appointment_date: string | null;
}
