import { apiClient as client } from './client';
import { Location, LocationListResponse, Pagination } from './types';

const BASE_PATH = '/api/v1/prm/locations';

export interface GetLocationsParams {
    page?: number;
    page_size?: number;
    search?: string;
    type?: string;
    is_active?: boolean;
    organization_id?: string;
}

export interface CreateLocationData {
    tenant_id: string;
    organization_id?: string;
    parent_location_id?: string;
    name: string;
    type?: string;
    code?: string;
    building?: string;
    floor?: string;
    room?: string;
    is_active: boolean;
    operational_status?: string;
    meta_data?: Record<string, any>;
}

export interface UpdateLocationData {
    organization_id?: string;
    parent_location_id?: string;
    name?: string;
    type?: string;
    code?: string;
    building?: string;
    floor?: string;
    room?: string;
    is_active?: boolean;
    operational_status?: string;
    meta_data?: Record<string, any>;
}

export async function getLocations(params: GetLocationsParams = {}): Promise<[LocationListResponse | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/locations`, { params });
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function getLocation(id: string): Promise<[Location | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/locations/${id}`);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function createLocation(data: CreateLocationData): Promise<[Location | null, any]> {
    try {
        const response = await client.post(`${BASE_PATH}/locations`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function updateLocation(id: string, data: UpdateLocationData): Promise<[Location | null, any]> {
    try {
        const response = await client.put(`${BASE_PATH}/locations/${id}`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}
