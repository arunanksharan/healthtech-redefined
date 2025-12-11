import { apiClient, PaginatedResponse, apiCall } from './client';
import type { Patient } from '@/lib/types';

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
    search?: string;
    org_id?: string;
  }) {
    return apiCall<PaginatedResponse<Patient>>(
      apiClient.get('/api/v1/prm/patients', { params })
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
    return apiCall<{
      patient: Patient;
      appointments: any[];
      journeys: any[];
      communications: any[];
      tickets: any[];
    }>(
      apiClient.get(`/api/v1/prm/patients/${id}/360`)
    );
  },
};
