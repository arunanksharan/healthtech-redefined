import { apiClient, apiCall } from './client';
import { Medication, MedicationListResponse } from './types';

const BASE_PATH = '/api/v1/prm/medications/medications';

interface GetMedicationsParams {
    page?: number;
    page_size?: number;
    patient_id?: string;
    status?: string;
    tenant_id?: string;
}

export const getMedications = async (params: GetMedicationsParams = {}) => {
    return apiCall<MedicationListResponse>(
        apiClient.get(BASE_PATH, { params })
    );
};

export const getMedication = async (id: string) => {
    return apiCall<Medication>(
        apiClient.get(`${BASE_PATH}/${id}`)
    );
};

export const createMedication = async (data: Partial<Medication>) => {
    return apiCall<Medication>(
        apiClient.post(BASE_PATH, data)
    );
};
