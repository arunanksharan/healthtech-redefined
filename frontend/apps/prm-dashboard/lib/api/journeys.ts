import { apiClient, apiCall } from './client';
import { Journey, JourneyListResponse, JourneyInstance, JourneyInstanceWithStages, JourneyInstanceStats, APIError } from '@/lib/api/types';

// ...

export const journeysAPI = {
  /**
   * Get all journeys
   */
  async getAll(params?: {
    page?: number;
    limit?: number;
    status?: string;
    patient_id?: string;
  }): Promise<[JourneyListResponse | null, APIError | null]> {
    return apiCall<JourneyListResponse>(
      apiClient.get('/api/v1/prm/journeys', { params })
    );
  },

  /**
   * Get journey instances (Patient Journeys)
   */
  async getInstances(params?: {
    page?: number;
    limit?: number;
    status?: string;
    patient_id?: string;
  }): Promise<[import('@/lib/api/types').JourneyInstanceListResponse | null, APIError | null]> {
    return apiCall<import('@/lib/api/types').JourneyInstanceListResponse>(
      apiClient.get('/api/v1/prm/instances', { params })
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
  /**
   * Create a new journey definition
   */
  async create(data: {
    tenant_id: string;
    name: string;
    description?: string;
    journey_type: string;
    is_default: boolean;
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

  /**
   * Get journey instance statistics
   * Used for dashboard "Active Journeys" card
   */
  async getInstanceStats(params?: {
    tenant_id?: string;
    journey_id?: string;
  }): Promise<[JourneyInstanceStats | null, APIError | null]> {
    return apiCall<JourneyInstanceStats>(
      apiClient.get('/api/v1/prm/instances/stats', { params })
    );
  },

  /**
   * Get journey instance by ID with stage statuses
   */
  async getInstance(instanceId: string): Promise<[JourneyInstanceWithStages | null, APIError | null]> {
    return apiCall<JourneyInstanceWithStages>(
      apiClient.get(`/api/v1/prm/instances/${instanceId}`)
    );
  },

  /**
   * Create a journey instance for a patient
   */
  async createInstance(data: {
    tenant_id: string;
    journey_id: string;
    patient_id: string;
  }): Promise<[JourneyInstance | null, APIError | null]> {
    return apiCall<JourneyInstance>(
      apiClient.post('/api/v1/prm/instances', data)
    );
  },

  /**
   * Advance journey instance to next stage
   */
  async advanceStage(
    instanceId: string,
    notes?: string
  ): Promise<[JourneyInstance | null, APIError | null]> {
    return apiCall<JourneyInstance>(
      apiClient.post(`/api/v1/prm/instances/${instanceId}/advance`, { notes })
    );
  },
};
