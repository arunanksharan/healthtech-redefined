import { z } from 'zod';

/**
 * Common validation schemas for the application
 */

// Phone number validation
export const phoneSchema = z
  .string()
  .regex(
    /^\+?[1-9]\d{1,14}$/,
    'Please enter a valid phone number with country code'
  );

// Email validation
export const emailSchema = z.string().email('Please enter a valid email address');

// Date validation
export const dateSchema = z.string().refine(
  (date) => !isNaN(Date.parse(date)),
  'Please enter a valid date'
);

// Patient schemas
export const patientSearchSchema = z.object({
  query: z.string().min(2, 'Search query must be at least 2 characters'),
  search_type: z.enum(['name', 'phone', 'email', 'mrn']).optional(),
});

export const createPatientSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  date_of_birth: dateSchema,
  gender: z.enum(['male', 'female', 'other']),
  phone: phoneSchema.optional(),
  email: emailSchema.optional(),
  address: z.string().optional(),
  medical_record_number: z.string().optional(),
});

export const updatePatientSchema = createPatientSchema.partial();

// Appointment schemas
export const createAppointmentSchema = z.object({
  patient_id: z.string().min(1, 'Patient ID is required'),
  scheduled_at: dateSchema,
  appointment_type: z.string().min(1, 'Appointment type is required'),
  duration: z.number().min(15, 'Duration must be at least 15 minutes').optional(),
  notes: z.string().optional(),
  practitioner_id: z.string().optional(),
});

export const rescheduleAppointmentSchema = z.object({
  scheduled_at: dateSchema,
});

export const cancelAppointmentSchema = z.object({
  cancellation_reason: z.string().min(3, 'Please provide a cancellation reason'),
});

// Journey schemas
export const createJourneySchema = z.object({
  patient_id: z.string().min(1, 'Patient ID is required'),
  journey_type: z.enum(['post_surgery', 'chronic_disease', 'wellness', 'pregnancy', 'other']),
  title: z.string().min(3, 'Title must be at least 3 characters'),
  description: z.string().optional(),
  expected_duration_days: z.number().min(1).optional(),
});

export const addJourneyStepSchema = z.object({
  title: z.string().min(3, 'Step title must be at least 3 characters'),
  description: z.string().optional(),
  order: z.number().min(1, 'Order must be at least 1'),
  due_date: dateSchema.optional(),
});

// Communication schemas
export const sendWhatsAppSchema = z.object({
  patient_id: z.string().min(1, 'Patient ID is required'),
  message: z.string().min(1, 'Message cannot be empty'),
  template_id: z.string().optional(),
});

export const sendSMSSchema = z.object({
  patient_id: z.string().min(1, 'Patient ID is required'),
  message: z.string().min(1, 'Message cannot be empty').max(160, 'SMS must be 160 characters or less'),
  template_id: z.string().optional(),
});

export const sendEmailSchema = z.object({
  patient_id: z.string().min(1, 'Patient ID is required'),
  subject: z.string().min(1, 'Subject is required'),
  message: z.string().min(1, 'Message cannot be empty'),
  template_id: z.string().optional(),
});

export const sendBulkCommunicationSchema = z.object({
  patient_ids: z.array(z.string()).min(1, 'At least one patient must be selected'),
  channel: z.enum(['whatsapp', 'sms', 'email']),
  subject: z.string().optional(),
  message: z.string().min(1, 'Message cannot be empty'),
  template_id: z.string().optional(),
});

// Ticket schemas
export const createTicketSchema = z.object({
  patient_id: z.string().optional(),
  title: z.string().min(3, 'Title must be at least 3 characters'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  category: z.enum(['billing', 'appointment', 'medical', 'technical', 'general']),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).optional(),
  assigned_to: z.string().optional(),
});

export const updateTicketSchema = z.object({
  title: z.string().min(3).optional(),
  description: z.string().min(10).optional(),
  status: z.enum(['open', 'in_progress', 'resolved', 'closed']).optional(),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).optional(),
  assigned_to: z.string().optional(),
});

export const addTicketCommentSchema = z.object({
  comment: z.string().min(1, 'Comment cannot be empty'),
  is_internal: z.boolean().optional(),
});

// Settings schemas
export const updateProfileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: emailSchema,
  phone: phoneSchema.optional(),
  role: z.string().optional(),
  department: z.string().optional(),
});

export const updateOrganizationSchema = z.object({
  name: z.string().min(2, 'Organization name must be at least 2 characters'),
  timezone: z.string(),
  language: z.string(),
  date_format: z.string(),
  time_format: z.enum(['12h', '24h']),
});

export const updateAISettingsSchema = z.object({
  openai_api_key: z.string().optional(),
  enable_ai: z.boolean(),
  auto_suggest: z.boolean(),
  confirm_high_risk: z.boolean(),
  max_agent_retries: z.number().min(1).max(5),
});

// Type inference
export type PatientSearchInput = z.infer<typeof patientSearchSchema>;
export type CreatePatientInput = z.infer<typeof createPatientSchema>;
export type UpdatePatientInput = z.infer<typeof updatePatientSchema>;
export type CreateAppointmentInput = z.infer<typeof createAppointmentSchema>;
export type RescheduleAppointmentInput = z.infer<typeof rescheduleAppointmentSchema>;
export type CancelAppointmentInput = z.infer<typeof cancelAppointmentSchema>;
export type CreateJourneyInput = z.infer<typeof createJourneySchema>;
export type AddJourneyStepInput = z.infer<typeof addJourneyStepSchema>;
export type SendWhatsAppInput = z.infer<typeof sendWhatsAppSchema>;
export type SendSMSInput = z.infer<typeof sendSMSSchema>;
export type SendEmailInput = z.infer<typeof sendEmailSchema>;
export type SendBulkCommunicationInput = z.infer<typeof sendBulkCommunicationSchema>;
export type CreateTicketInput = z.infer<typeof createTicketSchema>;
export type UpdateTicketInput = z.infer<typeof updateTicketSchema>;
export type AddTicketCommentInput = z.infer<typeof addTicketCommentSchema>;
export type UpdateProfileInput = z.infer<typeof updateProfileSchema>;
export type UpdateOrganizationInput = z.infer<typeof updateOrganizationSchema>;
export type UpdateAISettingsInput = z.infer<typeof updateAISettingsSchema>;
