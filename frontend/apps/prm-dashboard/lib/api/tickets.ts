import { apiClient, apiCall } from './client';
import { Ticket, TicketListResponse, APIError } from '@/lib/api/types';

// ...

export const ticketsAPI = {
  /**
   * Get all tickets
   */
  async getAll(params?: {
    page?: number;
    limit?: number;
    status?: string;
    category?: string;
    priority?: string;
    assigned_to?: string;
  }): Promise<[TicketListResponse | null, APIError | null]> {
    return apiCall<TicketListResponse>(
      apiClient.get('/api/v1/prm/tickets', { params })
    );
  },

  /**
   * Get ticket by ID
   */
  async getById(id: string): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(apiClient.get(`/api/v1/prm/tickets/${id}`));
  },

  /**
   * Get tickets for a patient
   */
  async getByPatient(
    patientId: string,
    status?: string
  ): Promise<[Ticket[] | null, APIError | null]> {
    return apiCall<Ticket[]>(
      apiClient.get(`/api/v1/prm/patients/${patientId}/tickets`, {
        params: { status },
      })
    );
  },

  /**
   * Create a new ticket
   */
  async create(data: {
    patient_id?: string;
    title: string;
    description: string;
    category: string;
    priority?: string;
    assigned_to?: string;
  }): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(apiClient.post('/api/v1/prm/tickets', data));
  },

  /**
   * Update ticket
   */
  async update(
    id: string,
    data: Partial<Ticket>
  ): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(apiClient.patch(`/api/v1/prm/tickets/${id}`, data));
  },

  /**
   * Assign ticket
   */
  async assign(
    id: string,
    assignedTo: string
  ): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(
      apiClient.patch(`/api/v1/prm/tickets/${id}`, {
        assigned_to: assignedTo,
      })
    );
  },

  /**
   * Resolve ticket
   */
  async resolve(
    id: string,
    resolutionNotes?: string
  ): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(
      apiClient.patch(`/api/v1/prm/tickets/${id}`, {
        status: 'resolved',
        resolution_notes: resolutionNotes,
      })
    );
  },

  /**
   * Close ticket
   */
  async close(id: string): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(
      apiClient.patch(`/api/v1/prm/tickets/${id}`, {
        status: 'closed',
      })
    );
  },

  /**
   * Reopen ticket
   */
  async reopen(id: string): Promise<[Ticket | null, APIError | null]> {
    return apiCall<Ticket>(
      apiClient.patch(`/api/v1/prm/tickets/${id}`, {
        status: 'open',
      })
    );
  },

  /**
   * Add comment to ticket
   */
  async addComment(
    ticketId: string,
    comment: string,
    isInternal: boolean = false
  ): Promise<[any | null, APIError | null]> {
    return apiCall<any>(
      apiClient.post(`/api/v1/prm/tickets/${ticketId}/comments`, {
        comment,
        is_internal: isInternal,
      })
    );
  },

  /**
   * Get ticket comments
   */
  async getComments(ticketId: string): Promise<[any[] | null, APIError | null]> {
    return apiCall<any[]>(
      apiClient.get(`/api/v1/prm/tickets/${ticketId}/comments`)
    );
  },
};
