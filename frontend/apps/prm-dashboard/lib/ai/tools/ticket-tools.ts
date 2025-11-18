import { Tool } from './types';
import { ticketsAPI } from '@/lib/api/tickets';

/**
 * Ticket Tools
 * Tools for managing support tickets through the AI assistant
 */

export const ticketTools: Tool[] = [
  /**
   * Create a new ticket
   */
  {
    name: 'ticket.create',
    description: 'Create a new support ticket',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: false,
      },
      title: {
        type: 'string',
        description: 'Ticket title',
        required: true,
      },
      description: {
        type: 'string',
        description: 'Detailed description of the issue',
        required: true,
      },
      category: {
        type: 'string',
        description: 'Ticket category',
        required: true,
        enum: ['billing', 'appointment', 'medical', 'technical', 'general'],
      },
      priority: {
        type: 'string',
        description: 'Ticket priority',
        required: false,
        enum: ['low', 'medium', 'high', 'urgent'],
        default: 'medium',
      },
      assigned_to: {
        type: 'string',
        description: 'User ID to assign ticket to',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [ticket, error] = await ticketsAPI.create({
          patient_id: params.patient_id,
          title: params.title,
          description: params.description,
          category: params.category,
          priority: params.priority || 'medium',
          assigned_to: params.assigned_to,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'TICKET_CREATE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: ticket,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TICKET_CREATE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Get ticket by ID
   */
  {
    name: 'ticket.get',
    description: 'Get detailed information about a ticket',
    parameters: {
      ticket_id: {
        type: 'string',
        description: 'ID of the ticket',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [ticket, error] = await ticketsAPI.getById(params.ticket_id);

        if (error) {
          return {
            success: false,
            error: {
              code: 'TICKET_NOT_FOUND',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: ticket,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TICKET_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Update ticket
   */
  {
    name: 'ticket.update',
    description: 'Update ticket information',
    parameters: {
      ticket_id: {
        type: 'string',
        description: 'ID of the ticket to update',
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
        const [ticket, error] = await ticketsAPI.update(
          params.ticket_id,
          params.updates
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'TICKET_UPDATE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: ticket,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TICKET_UPDATE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Assign ticket
   */
  {
    name: 'ticket.assign',
    description: 'Assign ticket to a user',
    parameters: {
      ticket_id: {
        type: 'string',
        description: 'ID of the ticket',
        required: true,
      },
      assigned_to: {
        type: 'string',
        description: 'User ID to assign to',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [ticket, error] = await ticketsAPI.assign(
          params.ticket_id,
          params.assigned_to
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'TICKET_ASSIGN_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: ticket,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TICKET_ASSIGN_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Resolve ticket
   */
  {
    name: 'ticket.resolve',
    description: 'Mark ticket as resolved',
    parameters: {
      ticket_id: {
        type: 'string',
        description: 'ID of the ticket to resolve',
        required: true,
      },
      resolution_notes: {
        type: 'string',
        description: 'Resolution notes',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [ticket, error] = await ticketsAPI.resolve(
          params.ticket_id,
          params.resolution_notes
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'TICKET_RESOLVE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: ticket,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TICKET_RESOLVE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Close ticket
   */
  {
    name: 'ticket.close',
    description: 'Close a ticket',
    parameters: {
      ticket_id: {
        type: 'string',
        description: 'ID of the ticket to close',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [ticket, error] = await ticketsAPI.close(params.ticket_id);

        if (error) {
          return {
            success: false,
            error: {
              code: 'TICKET_CLOSE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: ticket,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'TICKET_CLOSE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Add comment to ticket
   */
  {
    name: 'ticket.add_comment',
    description: 'Add a comment to a ticket',
    parameters: {
      ticket_id: {
        type: 'string',
        description: 'ID of the ticket',
        required: true,
      },
      comment: {
        type: 'string',
        description: 'Comment text',
        required: true,
      },
      is_internal: {
        type: 'boolean',
        description: 'Whether comment is internal (not visible to patient)',
        required: false,
        default: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [comment, error] = await ticketsAPI.addComment(
          params.ticket_id,
          params.comment,
          params.is_internal
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'COMMENT_ADD_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: comment,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'COMMENT_ADD_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },
];
