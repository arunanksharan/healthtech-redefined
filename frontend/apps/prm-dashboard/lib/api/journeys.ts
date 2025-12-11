import { apiClient, apiCall } from './client';
import { Journey, JourneyListResponse, APIError } from '@/lib/api/types';

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
    // MOCK DATA for Dashboard
    const mockInstances: import('@/lib/api/types').JourneyInstance[] = [
      {
        id: 'j1',
        tenant_id: 't1',
        journey_id: 'journey1',
        patient_id: 'p1',
        status: 'active',
        started_at: new Date(Date.now() - 86400000 * 2).toISOString(), // 2 days ago
        created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        updated_at: new Date().toISOString(),
        patient: { id: 'p1', name: 'John Doe', gender: 'male', date_of_birth: '1980-01-01' },
        journey: { id: 'journey1', name: 'Post-Surgery Recovery', title: 'Post-Surgery Recovery' },
        current_stage_id: 'stage2',
        context: { progress: 45 }
      },
      {
        id: 'j2',
        tenant_id: 't1',
        journey_id: 'journey2',
        patient_id: 'p2',
        status: 'completed',
        started_at: new Date(Date.now() - 86400000 * 10).toISOString(), // 10 days ago
        completed_at: new Date(Date.now() - 86400000).toISOString(), // Yesterday
        created_at: new Date(Date.now() - 86400000 * 10).toISOString(),
        updated_at: new Date().toISOString(),
        patient: { id: 'p2', name: 'Jane Smith', gender: 'female', date_of_birth: '1990-05-15' },
        journey: { id: 'journey2', name: 'Maternity Care', title: 'Maternity Care' },
        current_stage_id: 'stage_final',
        context: { progress: 100 }
      },
      {
        id: 'j3',
        tenant_id: 't1',
        journey_id: 'journey3',
        patient_id: 'p3',
        status: 'active',
        started_at: new Date().toISOString(), // Today
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        patient: { id: 'p3', name: 'Robert Johnson', gender: 'male', date_of_birth: '1975-08-20' },
        journey: { id: 'journey3', name: 'Chronic Diabetes Management', title: 'Chronic Diabetes Management' },
        current_stage_id: 'stage1',
        context: { progress: 15 }
      }
    ];

    return [
      {
        total: 3,
        instances: mockInstances,
        page: 1,
        page_size: 20,
        has_next: false,
        has_previous: false
      },
      null
    ];
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
