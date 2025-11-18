import { Tool } from './types';
import { communicationsAPI } from '@/lib/api/communications';

/**
 * Communication Tools
 * Tools for sending WhatsApp, SMS, and Email communications
 */

export const communicationTools: Tool[] = [
  /**
   * Send WhatsApp message
   */
  {
    name: 'communication.send_whatsapp',
    description: 'Send a WhatsApp message to a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      message: {
        type: 'string',
        description: 'Message content',
        required: true,
      },
      template_id: {
        type: 'string',
        description: 'WhatsApp template ID (optional)',
        required: false,
      },
      template_params: {
        type: 'object',
        description: 'Template parameters',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [communication, error] = await communicationsAPI.sendWhatsApp({
          patient_id: params.patient_id,
          message: params.message,
          template_id: params.template_id,
          template_params: params.template_params,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'WHATSAPP_SEND_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: communication,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'WHATSAPP_SEND_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Send SMS
   */
  {
    name: 'communication.send_sms',
    description: 'Send an SMS message to a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      message: {
        type: 'string',
        description: 'Message content',
        required: true,
      },
      phone_number: {
        type: 'string',
        description: 'Override phone number (optional)',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [communication, error] = await communicationsAPI.sendSMS({
          patient_id: params.patient_id,
          message: params.message,
          phone_number: params.phone_number,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'SMS_SEND_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: communication,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'SMS_SEND_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Send Email
   */
  {
    name: 'communication.send_email',
    description: 'Send an email to a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      subject: {
        type: 'string',
        description: 'Email subject',
        required: true,
      },
      body: {
        type: 'string',
        description: 'Email body (HTML or plain text)',
        required: true,
      },
      email_address: {
        type: 'string',
        description: 'Override email address (optional)',
        required: false,
      },
      template_id: {
        type: 'string',
        description: 'Email template ID (optional)',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [communication, error] = await communicationsAPI.sendEmail({
          patient_id: params.patient_id,
          subject: params.subject,
          body: params.body,
          email_address: params.email_address,
          template_id: params.template_id,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'EMAIL_SEND_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: communication,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'EMAIL_SEND_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Send bulk communication
   */
  {
    name: 'communication.send_bulk',
    description: 'Send bulk communication to multiple patients',
    parameters: {
      patient_ids: {
        type: 'array',
        description: 'Array of patient IDs',
        required: true,
      },
      channel: {
        type: 'string',
        description: 'Communication channel',
        required: true,
        enum: ['whatsapp', 'sms', 'email'],
      },
      message: {
        type: 'string',
        description: 'Message content',
        required: true,
      },
      subject: {
        type: 'string',
        description: 'Email subject (for email only)',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [result, error] = await communicationsAPI.sendBulk({
          patient_ids: params.patient_ids,
          channel: params.channel,
          message: params.message,
          subject: params.subject,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'BULK_SEND_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: result,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'BULK_SEND_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'high',
  },

  /**
   * Get communication templates
   */
  {
    name: 'communication.get_templates',
    description: 'Get available communication templates',
    parameters: {
      channel: {
        type: 'string',
        description: 'Filter by channel',
        required: false,
        enum: ['whatsapp', 'sms', 'email'],
      },
      category: {
        type: 'string',
        description: 'Filter by category',
        required: false,
        enum: ['appointment', 'reminder', 'follow_up', 'notification', 'marketing'],
      },
    },
    execute: async (params, context) => {
      try {
        const [templates, error] = await communicationsAPI.getTemplates(
          params.channel,
          params.category
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'TEMPLATES_FETCH_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: {
            templates,
            count: templates?.length || 0,
          },
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TEMPLATES_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Get communication history
   */
  {
    name: 'communication.get_history',
    description: 'Get communication history for a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      channel: {
        type: 'string',
        description: 'Filter by channel',
        required: false,
        enum: ['whatsapp', 'sms', 'email'],
      },
      limit: {
        type: 'number',
        description: 'Number of records to return',
        required: false,
        default: 50,
      },
    },
    execute: async (params, context) => {
      try {
        const [history, error] = await communicationsAPI.getHistory(
          params.patient_id,
          params.channel,
          params.limit
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'HISTORY_FETCH_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: {
            history,
            count: history?.length || 0,
          },
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'HISTORY_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },
];
