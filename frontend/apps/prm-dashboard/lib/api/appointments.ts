import { apiClient, PaginatedResponse, apiCall } from './client';
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
    // MOCK DATA for Dashboard
    const mockAppointments: Appointment[] = [
      {
        id: '1',
        patient_id: 'p1',
        patient: { id: 'p1', name: 'John Doe', mrn: 'MRN001', phone: '555-0101', date_of_birth: '1980-01-01', gender: 'male', created_at: '', updated_at: '' },
        practitioner_id: 'dr1',
        practitioner: { id: 'dr1', name: 'Dr. Sarah Wilson', speciality: 'Cardiology', qualification: 'MD' },
        start_time: new Date().toISOString(), // Today
        scheduled_at: new Date().toISOString(), // Same as start_time
        end_time: new Date(Date.now() + 30 * 60000).toISOString(),
        appointment_type: 'consultation',
        status: 'confirmed',
        location: { id: 'l1', name: 'Room 302' },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '2',
        patient_id: 'p2',
        patient: { id: 'p2', name: 'Jane Smith', mrn: 'MRN002', phone: '555-0102', date_of_birth: '1990-05-15', gender: 'female', created_at: '', updated_at: '' },
        practitioner_id: 'dr1',
        practitioner: { id: 'dr1', name: 'Dr. Sarah Wilson', speciality: 'Cardiology', qualification: 'MD' },
        start_time: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
        scheduled_at: new Date(Date.now() + 86400000).toISOString(), // Same as start_time
        end_time: new Date(Date.now() + 86400000 + 30 * 60000).toISOString(),
        appointment_type: 'follow_up',
        status: 'scheduled',
        location: { id: 'l1', name: 'Room 302' },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    ];

    return [
      {
        items: mockAppointments,
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1
      } as PaginatedResponse<Appointment>,
      null
    ];
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
