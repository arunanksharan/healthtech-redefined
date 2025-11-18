import { Tool } from './types';
import { journeysAPI } from '@/lib/api/journeys';

/**
 * Journey Tools
 * Tools for managing care journeys through the AI assistant
 */

export const journeyTools: Tool[] = [
  /**
   * Get journey by ID
   */
  {
    name: 'journey.get',
    description: 'Get detailed information about a journey',
    parameters: {
      journey_id: {
        type: 'string',
        description: 'ID of the journey',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [journey, error] = await journeysAPI.getById(params.journey_id);

        if (error) {
          return {
            success: false,
            error: {
              code: 'JOURNEY_NOT_FOUND',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: journey,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'JOURNEY_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Create a new journey
   */
  {
    name: 'journey.create',
    description: 'Create a new care journey for a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      journey_type: {
        type: 'string',
        description: 'Type of journey',
        required: true,
        enum: ['post_surgery', 'chronic_disease', 'wellness', 'pregnancy', 'other'],
      },
      template_id: {
        type: 'string',
        description: 'Journey template ID (optional)',
        required: false,
      },
      title: {
        type: 'string',
        description: 'Journey title',
        required: true,
      },
      description: {
        type: 'string',
        description: 'Journey description',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [journey, error] = await journeysAPI.create({
          patient_id: params.patient_id,
          journey_type: params.journey_type,
          template_id: params.template_id,
          title: params.title,
          description: params.description,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'JOURNEY_CREATE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: journey,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'JOURNEY_CREATE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Add a step to a journey
   */
  {
    name: 'journey.add_step',
    description: 'Add a new step to an existing journey',
    parameters: {
      journey_id: {
        type: 'string',
        description: 'ID of the journey',
        required: true,
      },
      step_title: {
        type: 'string',
        description: 'Title of the step',
        required: true,
      },
      step_description: {
        type: 'string',
        description: 'Description of the step',
        required: false,
      },
      step_type: {
        type: 'string',
        description: 'Type of step',
        required: false,
        enum: ['appointment', 'medication', 'test', 'follow_up', 'task', 'milestone'],
      },
      due_date: {
        type: 'string',
        description: 'Due date for the step (ISO 8601)',
        required: false,
      },
      assigned_to: {
        type: 'string',
        description: 'User/practitioner ID to assign',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [step, error] = await journeysAPI.addStep(params.journey_id, {
          title: params.step_title,
          description: params.step_description,
          step_type: params.step_type,
          due_date: params.due_date,
          assigned_to: params.assigned_to,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'STEP_ADD_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: step,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'STEP_ADD_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Complete a journey step
   */
  {
    name: 'journey.complete_step',
    description: 'Mark a journey step as completed',
    parameters: {
      journey_id: {
        type: 'string',
        description: 'ID of the journey',
        required: true,
      },
      step_id: {
        type: 'string',
        description: 'ID of the step to complete',
        required: true,
      },
      notes: {
        type: 'string',
        description: 'Completion notes',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [step, error] = await journeysAPI.completeStep(
          params.journey_id,
          params.step_id,
          params.notes
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'STEP_COMPLETE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: step,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'STEP_COMPLETE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Complete entire journey
   */
  {
    name: 'journey.complete',
    description: 'Mark an entire journey as completed',
    parameters: {
      journey_id: {
        type: 'string',
        description: 'ID of the journey to complete',
        required: true,
      },
      completion_notes: {
        type: 'string',
        description: 'Final completion notes',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [journey, error] = await journeysAPI.complete(
          params.journey_id,
          params.completion_notes
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'JOURNEY_COMPLETE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: journey,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'JOURNEY_COMPLETE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * List journeys for a patient
   */
  {
    name: 'journey.list_for_patient',
    description: 'Get all journeys for a specific patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      status: {
        type: 'string',
        description: 'Filter by status',
        required: false,
        enum: ['active', 'completed', 'paused', 'cancelled'],
      },
    },
    execute: async (params, context) => {
      try {
        const [journeys, error] = await journeysAPI.getByPatient(
          params.patient_id,
          params.status
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'JOURNEYS_FETCH_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: {
            journeys,
            count: journeys?.length || 0,
          },
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'JOURNEYS_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Update journey
   */
  {
    name: 'journey.update',
    description: 'Update journey information',
    parameters: {
      journey_id: {
        type: 'string',
        description: 'ID of the journey to update',
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
        const [journey, error] = await journeysAPI.update(
          params.journey_id,
          params.updates
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'JOURNEY_UPDATE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: journey,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'JOURNEY_UPDATE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },
];
