import { apiClient, apiCall } from './client';
import { Journey, PaginatedResponse, APIError } from '@/lib/types';

/**
 * Journeys API
 * All journey-related API operations
 */

export const journeysAPI = {
  /**
   * Get all journeys
   */
  async getAll(params?: {
    page?: number;
    limit?: number;
    status?: string;
    patient_id?: string;
  }): Promise<[PaginatedResponse<Journey> | null, APIError | null]> {
    return apiCall<PaginatedResponse<Journey>>(
      apiClient.get('/api/v1/prm/journeys', { params })
    );
  },

  /**
   * Get journey by ID
   */
  async getById(id: string): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(apiClient.get(`/api/v1/prm/journeys/${id}`));
  },

  /**
   * Get journeys for a patient
   */
  async getByPatient(
    patientId: string,
    status?: string
  ): Promise<[Journey[] | null, APIError | null]> {
    return apiCall<Journey[]>(
      apiClient.get(`/api/v1/prm/patients/${patientId}/journeys`, {
        params: { status },
      })
    );
  },

  /**
   * Create a new journey
   */
  async create(data: {
    patient_id: string;
    journey_type: string;
    template_id?: string;
    title: string;
    description?: string;
  }): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(apiClient.post('/api/v1/prm/journeys', data));
  },

  /**
   * Update journey
   */
  async update(
    id: string,
    data: Partial<Journey>
  ): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(apiClient.patch(`/api/v1/prm/journeys/${id}`, data));
  },

  /**
   * Add step to journey
   */
  async addStep(
    journeyId: string,
    data: {
      title: string;
      description?: string;
      step_type?: string;
      due_date?: string;
      assigned_to?: string;
    }
  ): Promise<[any | null, APIError | null]> {
    return apiCall<any>(
      apiClient.post(`/api/v1/prm/journeys/${journeyId}/steps`, data)
    );
  },

  /**
   * Complete a journey step
   */
  async completeStep(
    journeyId: string,
    stepId: string,
    notes?: string
  ): Promise<[any | null, APIError | null]> {
    return apiCall<any>(
      apiClient.patch(`/api/v1/prm/journeys/${journeyId}/steps/${stepId}`, {
        status: 'completed',
        completion_notes: notes,
      })
    );
  },

  /**
   * Complete entire journey
   */
  async complete(
    id: string,
    notes?: string
  ): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(
      apiClient.patch(`/api/v1/prm/journeys/${id}`, {
        status: 'completed',
        completion_notes: notes,
      })
    );
  },

  /**
   * Cancel journey
   */
  async cancel(
    id: string,
    reason?: string
  ): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(
      apiClient.patch(`/api/v1/prm/journeys/${id}`, {
        status: 'cancelled',
        cancellation_reason: reason,
      })
    );
  },

  /**
   * Pause journey
   */
  async pause(
    id: string,
    reason?: string
  ): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(
      apiClient.patch(`/api/v1/prm/journeys/${id}`, {
        status: 'paused',
        pause_reason: reason,
      })
    );
  },

  /**
   * Resume journey
   */
  async resume(id: string): Promise<[Journey | null, APIError | null]> {
    return apiCall<Journey>(
      apiClient.patch(`/api/v1/prm/journeys/${id}`, {
        status: 'active',
      })
    );
  },
};
