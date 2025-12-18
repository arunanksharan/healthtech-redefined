import { apiClient, PaginatedResponse, apiCall } from './client';
import type { Appointment, AppointmentSlot, AppointmentStats } from '@/lib/api/types';

/**
 * Appointment API Module
 * Complete API coverage for appointment management
 */

// ==================== Types ====================



export interface SlotSearchParams {
  conversation_id?: string;
  patient_phone?: string;
  practitioner_id?: string;
  specialty?: string;
  preferred_date?: string;
  preferred_time?: string;
  days_ahead?: number;
}

export interface ConflictCheckParams {
  practitioner_id: string;
  start_datetime: string;
  end_datetime: string;
  exclude_appointment_id?: string;
}

export interface AppointmentConflict {
  has_conflict: boolean;
  conflicting_appointments: Appointment[];
  message: string;
}

// ==================== API Methods ====================

export const appointmentsAPI = {
  /**
   * Get all appointments with filters
   */
  async getAll(params?: {
    page?: number;
    page_size?: number;
    practitioner_id?: string;
    patient_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }) {
    return apiCall<PaginatedResponse<Appointment>>(
      apiClient.get('/api/v1/prm/appointments', { params })
    );
  },

  /**
   * Get today's appointments
   */
  async getToday(params?: {
    practitioner_id?: string;
    status?: string;
  }) {
    return apiCall<Appointment[]>(
      apiClient.get('/api/v1/prm/appointments/today', { params })
    );
  },

  /**
   * Get upcoming appointments (next 7 days)
   */
  async getUpcoming(params?: {
    practitioner_id?: string;
    patient_id?: string;
    days?: number;
  }) {
    return apiCall<Appointment[]>(
      apiClient.get('/api/v1/prm/appointments/upcoming', { params })
    );
  },

  /**
   * Get appointment statistics
   */
  async getStats(params?: {
    start_date?: string;
    end_date?: string;
    practitioner_id?: string;
  }) {
    return apiCall<AppointmentStats>(
      apiClient.get('/api/v1/prm/appointments/stats', { params })
    );
  },

  /**
   * Get appointment by ID
   */
  async getById(id: string) {
    return apiCall<Appointment>(
      apiClient.get(`/api/v1/prm/appointments/${id}`)
    );
  },

  /**
   * Create new appointment (quick create from web form)
   */
  async create(data: {
    patient_id: string;
    practitioner_id: string;
    appointment_date: string;
    appointment_time: string;
    appointment_type: string;
    reason_text?: string;
  }) {
    return apiCall<Appointment>(
      apiClient.post('/api/v1/prm/appointments/quick', data)
    );
  },

  /**
   * Create appointment with full details (requires time_slot_id)
   */
  async createDirect(data: {
    tenant_id: string;
    patient_id: string;
    practitioner_id: string;
    location_id: string;
    time_slot_id: string;
    appointment_type?: string;
    reason_text?: string;
    source_channel?: string;
    meta_data?: Record<string, any>;
  }) {
    return apiCall<Appointment>(
      apiClient.post('/api/v1/prm/appointments', data)
    );
  },

  /**
   * Update appointment
   */
  async update(id: string, data: Partial<Appointment>) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}`, data)
    );
  },

  /**
   * Delete appointment
   */
  async delete(id: string) {
    return apiCall<void>(
      apiClient.delete(`/api/v1/prm/appointments/${id}`)
    );
  },

  /**
   * Cancel appointment (using dedicated endpoint)
   */
  async cancel(id: string, reason?: string) {
    return apiCall<Appointment>(
      apiClient.post(`/api/v1/prm/appointments/${id}/cancel`, {
        cancellation_reason: reason,
      })
    );
  },

  /**
   * Reschedule appointment
   */
  async reschedule(id: string, newSlotId: string, reason?: string) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}/reschedule`, {
        new_slot_id: newSlotId,
        reason,
      })
    );
  },

  /**
   * Find available slots for booking
   */
  async findSlots(params: SlotSearchParams) {
    return apiCall<{
      conversation_id: string;
      slots: AppointmentSlot[];
      message_to_user: string;
      total_slots: number;
    }>(
      apiClient.post('/api/v1/prm/appointments/find-slots', params)
    );
  },

  /**
   * Get available slots (GET method for simpler queries)
   */
  async getAvailableSlots(params: {
    practitioner_id?: string;
    speciality?: string;
    date_start: string;
    date_end: string;
    location_id?: string;
    duration?: number;
  }) {
    return apiCall<AppointmentSlot[]>(
      apiClient.get('/api/v1/prm/appointments/slots', { params })
    );
  },

  /**
   * Check for appointment conflicts
   */
  async checkConflicts(params: ConflictCheckParams) {
    return apiCall<AppointmentConflict>(
      apiClient.get('/api/v1/prm/appointments/conflicts', { params })
    );
  },

  /**
   * Handle slot selection from conversation flow
   */
  async selectSlot(data: {
    conversation_id: string;
    user_text: string;
    available_slots: AppointmentSlot[];
  }) {
    return apiCall<{
      success: boolean;
      message: string;
      action: string;
      appointment_id?: string;
      needs_clarification: boolean;
      follow_up_message?: string;
    }>(
      apiClient.post('/api/v1/prm/appointments/select-slot', data)
    );
  },

  /**
   * Check in patient for appointment
   */
  async checkIn(id: string) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}`, {
        status: 'checked_in',
      })
    );
  },

  /**
   * Mark appointment as complete
   */
  async complete(id: string, notes?: string) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}`, {
        status: 'completed',
        notes,
      })
    );
  },

  /**
   * Mark patient as no-show
   */
  async markNoShow(id: string) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}`, {
        status: 'no_show',
      })
    );
  },

  /**
   * Confirm appointment
   */
  async confirm(id: string) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}`, {
        status: 'confirmed',
      })
    );
  },
};

