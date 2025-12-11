import { apiClient, apiCall } from './client';
import { Communication, PaginatedResponse, APIError } from '@/lib/types';

/**
 * Communications API
 * All communication-related API operations (WhatsApp, SMS, Email)
 */

export const communicationsAPI = {
  /**
   * Send WhatsApp message
   */
  async sendWhatsApp(data: {
    patient_id: string;
    message: string;
    template_id?: string;
    template_params?: Record<string, any>;
  }): Promise<[Communication | null, APIError | null]> {
    return apiCall<Communication>(
      apiClient.post('/api/v1/prm/communications/whatsapp', data)
    );
  },

  /**
   * Send SMS
   */
  async sendSMS(data: {
    patient_id: string;
    message: string;
    phone_number?: string;
  }): Promise<[Communication | null, APIError | null]> {
    return apiCall<Communication>(
      apiClient.post('/api/v1/prm/communications/sms', data)
    );
  },

  /**
   * Send Email
   */
  async sendEmail(data: {
    patient_id: string;
    subject: string;
    body: string;
    email_address?: string;
    template_id?: string;
  }): Promise<[Communication | null, APIError | null]> {
    return apiCall<Communication>(
      apiClient.post('/api/v1/prm/communications/email', data)
    );
  },

  /**
   * Send bulk communication
   */
  async sendBulk(data: {
    patient_ids: string[];
    channel: 'whatsapp' | 'sms' | 'email';
    message: string;
    subject?: string;
  }): Promise<[any | null, APIError | null]> {
    return apiCall<any>(
      apiClient.post('/api/v1/prm/communications/bulk', data)
    );
  },

  /**
   * Get all communications
   */
  async getAll(params?: {
    page?: number;
    limit?: number;
    channel?: string;
    status?: string;
  }): Promise<[CommunicationListResponse | null, APIError | null]> {
    // Map frontend 'limit' to backend 'page_size'
    const queryParams: any = {
      page: params?.page || 1,
      page_size: params?.limit || 20,
      ...params
    };
    delete queryParams.limit; // Remove limit to avoid confusion if strict

    return apiCall<CommunicationListResponse>(
      apiClient.get('/api/v1/prm/communications', { params: queryParams })
    );
  },

  /**
   * Get communication by ID
   */
  async getById(id: string): Promise<[Communication | null, APIError | null]> {
    return apiCall<Communication>(
      apiClient.get(`/api/v1/prm/communications/${id}`)
    );
  },

  /**
   * Get communication history for a patient
   */
  async getHistory(
    patientId: string,
    channel?: string,
    limit: number = 50
  ): Promise<[Communication[] | null, APIError | null]> {
    return apiCall<Communication[]>(
      apiClient.get(`/api/v1/prm/patients/${patientId}/communications`, {
        params: { channel, limit },
      })
    );
  },

  /**
   * Get communication templates
   */
  async getTemplates(
    channel?: string,
    category?: string
  ): Promise<[any[] | null, APIError | null]> {
    return apiCall<any[]>(
      apiClient.get('/api/v1/prm/communications/templates', {
        params: { channel, category },
      })
    );
  },

  /**
   * Create communication template
   */
  async createTemplate(data: {
    name: string;
    channel: 'whatsapp' | 'sms' | 'email';
    category: string;
    content: string;
    variables?: string[];
  }): Promise<[any | null, APIError | null]> {
    return apiCall<any>(
      apiClient.post('/api/v1/prm/communications/templates', data)
    );
  },

  /**
   * Update communication status
   */
  async updateStatus(
    id: string,
    status: string
  ): Promise<[Communication | null, APIError | null]> {
    return apiCall<Communication>(
      apiClient.patch(`/api/v1/prm/communications/${id}`, { status })
    );
  },
};
