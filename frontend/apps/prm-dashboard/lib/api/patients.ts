import { apiClient, PaginatedResponse, apiCall } from './client';
import type { Patient } from '@/lib/types';
import type { Patient360Response } from './types';

/**
 * Patient API Module
 * All patient-related API calls using modern patterns
 */

export const patientsAPI = {
  /**
   * Get all patients with optional filters
   */
  async getAll(params?: {
    page?: number;
    page_size?: number;
    limit?: number;
    search?: string;
    org_id?: string;
  }) {
    // Map 'limit' to 'page_size' for backend compatibility
    const queryParams = {
      page: params?.page || 1,
      page_size: params?.limit || params?.page_size || 20,
      search: params?.search,
      org_id: params?.org_id,
    };

    return apiCall<{
      items: Patient[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(
      apiClient.get('/api/v1/prm/patients', { params: queryParams })
    );
  },

  /**
   * Get a single patient by ID
   */
  async getById(id: string) {
    return apiCall<Patient>(
      apiClient.get(`/api/v1/prm/patients/${id}`)
    );
  },

  /**
   * Create a new patient
   */
  async create(data: Partial<Patient>) {
    return apiCall<Patient>(
      apiClient.post('/api/v1/prm/patients', data)
    );
  },

  /**
   * Update a patient
   */
  async update(id: string, data: Partial<Patient>) {
    return apiCall<Patient>(
      apiClient.patch(`/api/v1/prm/patients/${id}`, data)
    );
  },

  /**
   * Delete a patient
   */
  async delete(id: string) {
    return apiCall<void>(
      apiClient.delete(`/api/v1/prm/patients/${id}`)
    );
  },

  /**
   * Search patients by phone, name, or MRN
   */
  async search(query: string, type?: 'phone' | 'name' | 'mrn') {
    return apiCall<Patient[]>(
      apiClient.get('/api/v1/prm/patients/search', {
        params: { query, type },
      })
    );
  },

  /**
   * Get patient 360° view with all related data
   */
  async get360View(id: string) {
    return apiCall<Patient360Response>(
      apiClient.get(`/api/v1/prm/patients/${id}/360`)
    );
  },

  /**
   * Get patient demographics and statistics
   */
  async getStats(orgId?: string) {
    return apiCall<PatientStatistics>(
      apiClient.get('/api/v1/prm/patients/stats/demographics', {
        params: orgId ? { org_id: orgId } : undefined,
      })
    );
  },

  /**
   * Get all appointments for a patient
   */
  async getAppointments(patientId: string) {
    return apiCall<PatientAppointment[]>(
      apiClient.get(`/api/v1/prm/patients/${patientId}/appointments`)
    );
  },

  /**
   * Get all conversations for a patient
   */
  async getConversations(patientId: string) {
    return apiCall<PatientConversation[]>(
      apiClient.get(`/api/v1/prm/patients/${patientId}/conversations`)
    );
  },

  /**
   * Reactivate an inactive patient
   */
  async activate(patientId: string) {
    return apiCall<Patient>(
      apiClient.post(`/api/v1/prm/patients/${patientId}/activate`)
    );
  },

  /**
   * Find potential duplicate patients
   */
  async findDuplicates(patientId: string) {
    return apiCall<DuplicatePatient[]>(
      apiClient.get(`/api/v1/prm/patients/${patientId}/duplicates`)
    );
  },
};

// ==================== Type Definitions ====================

export interface PatientStatistics {
  total_patients: number;
  active_patients: number;
  inactive_patients: number;
  new_this_month: number;
  by_gender: Record<string, number>;
  by_age_group: Record<string, number>;
  by_status: Record<string, number>;
  average_age: number;
}

export interface PatientAppointment {
  id: string;
  patient_id: string;
  practitioner_id: string;
  location_id: string;
  time_slot_id: string;
  appointment_type: string;
  status: string;
  reason_text?: string;
  source_channel?: string;
  created_at: string;
  updated_at: string;
}

export interface PatientConversation {
  id: string;
  patient_id: string;
  channel: string;
  direction: string;
  template_code?: string;
  content?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DuplicatePatient {
  patient_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_primary?: string;
  match_score: number;
  match_reasons: string[];
}
