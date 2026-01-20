import { apiClient as client } from './client';
import { Encounter, EncounterListResponse } from './types';

const BASE_PATH = '/api/v1/prm/encounters';

export interface GetEncountersParams {
    page?: number;
    page_size?: number;
    patient_id?: string;
    practitioner_id?: string;
    status?: string;
    class_code?: string;
    date_from?: string;
    date_to?: string;
}

export interface CreateEncounterData {
    tenant_id: string;
    patient_id: string;
    practitioner_id: string;
    appointment_id?: string;
    encounter_fhir_id?: string;
    status: string;
    class_code: string;
    started_at?: string;
    ended_at?: string;
}

export interface UpdateEncounterData {
    status?: string;
    class_code?: string;
    started_at?: string;
    ended_at?: string;
}

export async function getEncounters(params: GetEncountersParams = {}): Promise<[EncounterListResponse | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/encounters`, { params });
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function getEncounter(id: string): Promise<[Encounter | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/encounters/${id}`);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function createEncounter(data: CreateEncounterData): Promise<[Encounter | null, any]> {
    try {
        const response = await client.post(`${BASE_PATH}/encounters`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function updateEncounter(id: string, data: UpdateEncounterData): Promise<[Encounter | null, any]> {
    try {
        const response = await client.put(`${BASE_PATH}/encounters/${id}`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}
