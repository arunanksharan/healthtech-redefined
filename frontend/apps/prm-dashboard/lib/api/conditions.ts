import { apiClient as client } from './client';
import { Condition, ConditionListResponse, ConditionCode } from './types';

const BASE_PATH = '/api/v1/prm/conditions';

export interface GetConditionsParams {
    page?: number;
    page_size?: number;
    patient_id?: string;
    clinical_status?: string;
    category?: string;
    tenant_id?: string;
}

export interface CreateConditionData {
    tenant_id: string;
    patient_id: string;
    encounter_id?: string;
    recorder_id?: string;
    clinical_status: string;
    verification_status: string;
    category: string;
    severity?: string;
    code: ConditionCode;
    onset_datetime?: string;
    abatement_datetime?: string;
    note?: string;
}

export async function getConditions(params: GetConditionsParams = {}): Promise<[ConditionListResponse | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/conditions`, { params });
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function getCondition(id: string): Promise<[Condition | null, any]> {
    try {
        const response = await client.get(`${BASE_PATH}/conditions/${id}`);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export async function createCondition(data: CreateConditionData): Promise<[Condition | null, any]> {
    try {
        const response = await client.post(`${BASE_PATH}/conditions`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}

export interface UpdateConditionData {
    clinical_status?: string;
    verification_status?: string;
    severity?: string;
    abatement_datetime?: string;
    note?: string;
}

export async function updateCondition(id: string, data: UpdateConditionData): Promise<[Condition | null, any]> {
    try {
        const response = await client.put(`${BASE_PATH}/conditions/${id}`, data);
        return [response.data, null];
    } catch (error) {
        return [null, error];
    }
}
