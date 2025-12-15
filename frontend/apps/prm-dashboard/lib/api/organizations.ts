
import { apiClient, apiCall, APIResponse, PaginatedResponse } from './client';
import { Organization, OrganizationListResponse } from './types';

const BASE_PATH = '/api/v1/prm/organizations';

/**
 * List organizations with filtering and pagination
 */
export async function getOrganizations(params?: {
    page?: number;
    page_size?: number;
    type?: string;
    is_active?: boolean;
}) {
    return apiCall<OrganizationListResponse>(
        // router defines @router.get("") so it maps to .../organizations/organizations if main adds prefix.
        // However, usually one prefix is enough.
        // If backend router.py has prefix="/organizations", and main.py has prefix="/api/v1/prm/organizations",
        // then the URL is indeed .../organizations/organizations.
        // The previous implementation used BASE_PATH/organizations which means .../organizations/organizations.
        // THIS SEEMS CORRECT based on code inspection.
        apiClient.get(`${BASE_PATH}/organizations`, { params })
    );
}

/**
 * Get a single organization by ID
 */
export async function getOrganization(id: string) {
    return apiCall<Organization>(
        apiClient.get(`${BASE_PATH}/organizations/${id}`)
    );
}

/**
 * Create a new organization
 */
export async function createOrganization(data: Partial<Organization>) {
    return apiCall<Organization>(
        apiClient.post(`${BASE_PATH}/organizations`, data)
    );
}

/**
 * Update an existing organization
 */
export async function updateOrganization(id: string, data: Partial<Organization>) {
    return apiCall<Organization>(
        apiClient.put(`${BASE_PATH}/organizations/${id}`, data)
    );
}

/**
 * Delete an organization
 */
export async function deleteOrganization(id: string) {
    return apiCall<void>(
        apiClient.delete(`${BASE_PATH}/organizations/${id}`)
    );
}
