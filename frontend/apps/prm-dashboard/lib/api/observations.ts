import { apiClient as client } from './client';
import { Observation, ObservationListResponse, ObservationCode, ObservationValue } from './types';

const BASE_PATH = '/api/v1/prm/observations';

export interface GetObservationsParams {
    page?: number;
    page_size?: number;
    patient_id?: string;
    encounter_id?: string;
    category?: string;
    code?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
}

export interface CreateObservationData {
    tenant_id: string;
    patient_id: string;
    encounter_id?: string;
    practitioner_id?: string;
    status: string;
    category: string;
    code: ObservationCode;
    value?: ObservationValue;
    effective_datetime?: string;
    interpretation?: string;
    note?: string;
}

export async function getObservations(params: GetObservationsParams = {}): Promise<[ObservationListResponse | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/observations`, { params });
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function getObservation(id: string): Promise<[Observation | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/observations/${id}`);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function createObservation(data: CreateObservationData): Promise<[Observation | null, any]> {
    try {
        const response = await client.post(`${BASE_PATH}/observations`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}
