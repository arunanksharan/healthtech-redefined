import { Tool } from './types';
import { appointmentsAPI } from '@/lib/api/appointments';
import { patientsAPI } from '@/lib/api/patients';

/**
 * Appointment Tools
 * Tools for managing appointments through the AI assistant
 */

export const appointmentTools: Tool[] = [
  /**
   * Check available appointment slots
   */
  {
    name: 'appointment.check_availability',
    description: 'Check available appointment slots for a practitioner or speciality',
    parameters: {
      practitioner_id: {
        type: 'string',
        description: 'ID of the practitioner',
        required: false,
      },
      speciality: {
        type: 'string',
        description: 'Medical speciality (e.g., cardiology, orthopaedics)',
        required: false,
      },
      date_start: {
        type: 'string',
        description: 'Start date for availability check (ISO 8601 format)',
        required: true,
      },
      date_end: {
        type: 'string',
        description: 'End date for availability check (ISO 8601 format)',
        required: true,
      },
      location_id: {
        type: 'string',
        description: 'Clinic/hospital location ID',
        required: false,
      },
      duration: {
        type: 'number',
        description: 'Appointment duration in minutes',
        required: false,
        default: 30,
      },
    },
    execute: async (params, context) => {
      try {
        const [slots, error] = await appointmentsAPI.getAvailableSlots({
          practitioner_id: params.practitioner_id,
          speciality: params.speciality,
          date_start: params.date_start,
          date_end: params.date_end,
          location_id: params.location_id,
          duration: params.duration || 30,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'AVAILABILITY_CHECK_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: {
            slots,
            count: slots?.length || 0,
          },
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'AVAILABILITY_CHECK_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },

  /**
   * Book an appointment
   */
  {
    name: 'appointment.book',
    description: 'Book a new appointment for a patient',
    parameters: {
      patient_id: {
        type: 'string',
        description: 'ID of the patient',
        required: true,
      },
      practitioner_id: {
        type: 'string',
        description: 'ID of the practitioner',
        required: true,
      },
      slot_id: {
        type: 'string',
        description: 'ID of the available slot to book',
        required: true,
      },
      appointment_type: {
        type: 'string',
        description: 'Type of appointment',
        required: true,
        enum: ['consultation', 'follow_up', 'procedure', 'test'],
      },
      notes: {
        type: 'string',
        description: 'Additional notes for the appointment',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [appointment, error] = await appointmentsAPI.create({
          patient_id: params.patient_id,
          practitioner_id: params.practitioner_id,
          slot_id: params.slot_id,
          appointment_type: params.appointment_type,
          notes: params.notes,
        });

        if (error) {
          return {
            success: false,
            error: {
              code: 'BOOKING_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: appointment,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'BOOKING_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Cancel an appointment
   */
  {
    name: 'appointment.cancel',
    description: 'Cancel an existing appointment',
    parameters: {
      appointment_id: {
        type: 'string',
        description: 'ID of the appointment to cancel',
        required: true,
      },
      reason: {
        type: 'string',
        description: 'Reason for cancellation',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [appointment, error] = await appointmentsAPI.cancel(
          params.appointment_id,
          params.reason
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'CANCELLATION_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: appointment,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'CANCELLATION_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Reschedule an appointment
   */
  {
    name: 'appointment.reschedule',
    description: 'Reschedule an existing appointment to a new slot',
    parameters: {
      appointment_id: {
        type: 'string',
        description: 'ID of the appointment to reschedule',
        required: true,
      },
      new_slot_id: {
        type: 'string',
        description: 'ID of the new slot',
        required: true,
      },
      reason: {
        type: 'string',
        description: 'Reason for rescheduling',
        required: false,
      },
    },
    execute: async (params, context) => {
      try {
        const [appointment, error] = await appointmentsAPI.reschedule(
          params.appointment_id,
          params.new_slot_id,
          params.reason
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'RESCHEDULE_FAILED',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: appointment,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'RESCHEDULE_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: true,
    riskLevel: 'medium',
  },

  /**
   * Get appointment details
   */
  {
    name: 'appointment.get',
    description: 'Get details of a specific appointment',
    parameters: {
      appointment_id: {
        type: 'string',
        description: 'ID of the appointment',
        required: true,
      },
    },
    execute: async (params, context) => {
      try {
        const [appointment, error] = await appointmentsAPI.getById(
          params.appointment_id
        );

        if (error) {
          return {
            success: false,
            error: {
              code: 'APPOINTMENT_NOT_FOUND',
              message: error.message,
              details: error,
            },
          };
        }

        return {
          success: true,
          data: appointment,
        };
      } catch (error: any) {
        return {
          success: false,
          error: {
            code: 'APPOINTMENT_FETCH_ERROR',
            message: error.message,
          },
        };
      }
    },
    requiresConfirmation: false,
    riskLevel: 'low',
  },
];
