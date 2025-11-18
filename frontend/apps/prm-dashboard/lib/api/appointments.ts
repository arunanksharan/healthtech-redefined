import apiClient, { PaginatedResponse, apiCall } from './client';
import type { Appointment, AppointmentSlot } from '@/lib/types';

/**
 * Appointment API Module
 * Using latest patterns with proper error handling
 */

export const appointmentsAPI = {
  /**
   * Get all appointments
   */
  async getAll(params?: {
    page?: number;
    page_size?: number;
    practitioner_id?: string;
    patient_id?: string;
    status?: string;
    date_start?: string;
    date_end?: string;
  }) {
    return apiCall<PaginatedResponse<Appointment>>(
      apiClient.get('/api/v1/prm/appointments', { params })
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
   * Create new appointment
   */
  async create(data: {
    patient_id: string;
    practitioner_id: string;
    slot_id: string;
    appointment_type: string;
    notes?: string;
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
   * Cancel appointment
   */
  async cancel(id: string, reason?: string) {
    return apiCall<Appointment>(
      apiClient.patch(`/api/v1/prm/appointments/${id}`, {
        status: 'cancelled',
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
   * Get available slots
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
};
