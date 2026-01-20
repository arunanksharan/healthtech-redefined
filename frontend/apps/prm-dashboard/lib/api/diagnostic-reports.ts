import { apiClient, apiCall } from './client';
import { DiagnosticReport, ReportListResponse } from './types';


const BASE_PATH = '/api/v1/prm/diagnostic-reports/diagnostic-reports';


interface GetReportsParams {
    page?: number;
    page_size?: number;
    patient_id?: string;
    category?: string;
    status?: string;
    tenant_id?: string;
}

export const getDiagnosticReports = async (params: GetReportsParams = {}) => {
    return apiCall<ReportListResponse>(
        apiClient.get(BASE_PATH, { params })
    );
};

export const getDiagnosticReport = async (id: string) => {
    return apiCall<DiagnosticReport>(
        apiClient.get(`${BASE_PATH}/${id}`)
    );
};

export const createDiagnosticReport = async (data: Partial<DiagnosticReport>) => {
    return apiCall<DiagnosticReport>(
        apiClient.post(BASE_PATH, data)
    );
};
