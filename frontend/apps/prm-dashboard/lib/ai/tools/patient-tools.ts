import { Tool } from './types';
import { patientsAPI } from '@/lib/api/patients';

/**
 * Patient Tools
 * Tools for managing patients through the AI assistant
 */

export const patientTools: Tool[] = [
  /**
   * Search for patients
   */
  {
    name: 'patient.search',
    description: 'Search for patients by phone number, name, or MRN',
    parameters: {
      query: {
        type: 'string',
        description: 'Search query (phone, name, or MRN)',
        required: true,
      },
      search_type: {
        type: 'string',
        description: 'Type of search',
        required: false,
        enum: ['phone', 'name', 'mrn'],
      },
    },
    execute: async (params, context) => {
      try {
        const [patients, error] = await patientsAPI.search(
          params.query,
          params.search_type
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'SEARCH_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: {
            patients,
            count: patients?.length || 0,
          },
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'SEARCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Get patient by ID
   */
  {
    name: 'patient.get',
    description: 'Get detailed information about a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [patient, error] = await patientsAPI.getById(params.patient_id);

        if (error) {
          return {
            success: false,
            error: {
              code: 'PATIENT_NOT_FOUND',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: patient,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'PATIENT_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Get patient 360° view
   */
  {
    name: 'patient.get_360_view',
    description: 'Get complete 360° view of a patient including all related data',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [view, error] = await patientsAPI.get360View(params.patient_id);

        if (error) {
          return {
            success: false,
            error: {
              code: '360_VIEW_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: view,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: '360_VIEW_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Create a new patient
   */
  {
    name: 'patient.create',
    description: 'Create a new patient record',
    parameters: {
      name: {
        type: 'string',
        description: 'Patient name',
        required: true,
      },
      phone: {
        type: 'string',
        description: 'Patient phone number',
        required: true,
      },
      email: {
        type: 'string',
        description: 'Patient email',
        required: false,
      },
      date_of_birth: {
        type: 'string',
        description: 'Date of birth (ISO 8601)',
        required: false,
      },
      gender: {
        type: 'string',
        description: 'Patient gender',
        required: false,
        enum: ['male', 'female', 'other'],
      },
    },
    execute: async (params, context) => {
      try {
        const [patient, error] = await patientsAPI.create(params);

        if (error) {
          return {
            success: false,
            error: {
              code: 'PATIENT_CREATE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: patient,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'PATIENT_CREATE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Update patient information
   */
  {
    name: 'patient.update',
    description: 'Update patient information',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient to update',
        required: true,
      },
      updates: {
        type: 'object',
        description: 'Fields to update',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [patient, error] = await patientsAPI.update(
          params.patient_id,
          params.updates
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'PATIENT_UPDATE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: patient,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'PATIENT_UPDATE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },
];
