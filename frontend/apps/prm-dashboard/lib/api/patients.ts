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
    // MOCK DATA for Dashboard
    const mockPatients: Patient[] = [
      { id: 'p1', name: 'John Doe', mrn: 'MRN001', phone: '555-0101', email: 'john@example.com', date_of_birth: '1980-01-01', gender: 'male', created_at: '', updated_at: '' },
      { id: 'p2', name: 'Jane Smith', mrn: 'MRN002', phone: '555-0102', email: 'jane@example.com', date_of_birth: '1990-05-15', gender: 'female', created_at: '', updated_at: '' },
      { id: 'p3', name: 'Robert Johnson', mrn: 'MRN003', phone: '555-0103', email: 'bob@example.com', date_of_birth: '1975-11-20', gender: 'male', created_at: '', updated_at: '' },
    ];

    return [
      {
        items: mockPatients,
        total: 3,
        page: 1,
        page_size: 20,
        total_pages: 1
      } as PaginatedResponse<Patient>,
      null
    ];
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
