import { apiClient, apiCall } from './client';

/**
 * Practitioners API Module
 * Healthcare provider management endpoints
 */

// ==================== Types ====================

export interface Practitioner {
    id: string;
    tenant_id: string;
    first_name: string;
    last_name: string;
    middle_name?: string;
    gender?: string;
    qualification?: string;
    speciality?: string;
    sub_speciality?: string;
    license_number?: string;
    registration_number?: string;
    phone_primary?: string;
    email_primary?: string;
    is_active: boolean;
    meta_data?: Record<string, any>;
    created_at: string;
    updated_at: string;
}

export interface PractitionerSimple {
    id: string;
    name: string;
    speciality?: string;
    is_active: boolean;
}

export interface PractitionerListResponse {
    items: Practitioner[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
}

export interface PractitionerCreate {
    tenant_id: string;
    first_name: string;
    last_name: string;
    middle_name?: string;
    gender?: string;
    qualification?: string;
    speciality?: string;
    sub_speciality?: string;
    license_number?: string;
    registration_number?: string;
    phone_primary?: string;
    email_primary?: string;
    is_active?: boolean;
    meta_data?: Record<string, any>;
}

export interface PractitionerUpdate {
    first_name?: string;
    last_name?: string;
    middle_name?: string;
    gender?: string;
    qualification?: string;
    speciality?: string;
    sub_speciality?: string;
    license_number?: string;
    registration_number?: string;
    phone_primary?: string;
    email_primary?: string;
    is_active?: boolean;
    meta_data?: Record<string, any>;
}

// ==================== API Methods ====================

export const practitionersAPI = {
    /**
     * List practitioners with pagination and filters
     */
    async getAll(params?: {
        page?: number;
        page_size?: number;
        tenant_id?: string;
        speciality?: string;
        is_active?: boolean;
        search?: string;
    }) {
        const queryParams = {
            page: params?.page || 1,
            page_size: params?.page_size || 20,
            ...params,
        };

        return apiCall<PractitionerListResponse>(
            apiClient.get('/api/v1/prm/practitioners', { params: queryParams })
        );
    },

    /**
     * Get simplified list for dropdowns
     */
    async getSimple(params?: {
        tenant_id?: string;
        speciality?: string;
        active_only?: boolean;
    }) {
        return apiCall<PractitionerSimple[]>(
            apiClient.get('/api/v1/prm/practitioners/simple', { params })
        );
    },

    /**
     * Get list of unique specialities
     */
    async getSpecialities(tenant_id?: string) {
        return apiCall<string[]>(
            apiClient.get('/api/v1/prm/practitioners/specialities', {
                params: tenant_id ? { tenant_id } : undefined,
            })
        );
    },

    /**
     * Get practitioner by ID
     */
    async getById(id: string) {
        return apiCall<Practitioner>(
            apiClient.get(`/api/v1/prm/practitioners/${id}`)
        );
    },

    /**
     * Create a new practitioner
     */
    async create(data: PractitionerCreate) {
        return apiCall<Practitioner>(
            apiClient.post('/api/v1/prm/practitioners', data)
        );
    },

    /**
     * Update a practitioner
     */
    async update(id: string, data: PractitionerUpdate) {
        return apiCall<Practitioner>(
            apiClient.patch(`/api/v1/prm/practitioners/${id}`, data)
        );
    },

    /**
     * Delete a practitioner
     */
    async delete(id: string) {
        return apiCall<void>(
            apiClient.delete(`/api/v1/prm/practitioners/${id}`)
        );
    },
};
