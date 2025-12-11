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
