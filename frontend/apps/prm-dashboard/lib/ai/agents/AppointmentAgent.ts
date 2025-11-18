import { BaseAgent, AgentPlan, AgentResult } from './BaseAgent';
import { ExecutionContext, ToolResult } from '../tools/types';
import { toolRegistry } from '../tools/registry';

/**
 * AppointmentAgent
 * Specialized agent for handling all appointment-related operations
 *
 * Capabilities:
 * - Check appointment availability
 * - Book new appointments
 * - Cancel appointments
 * - Reschedule appointments
 * - Retrieve appointment details
 */
export class AppointmentAgent extends BaseAgent {
  constructor(openaiApiKey?: string) {
    super(
      'AppointmentAgent',
      'an AI assistant specialized in managing healthcare appointments',
      [
        'appointment.check_availability',
        'appointment.book',
        'appointment.cancel',
        'appointment.reschedule',
        'appointment.get',
        'patient.search', // Needed to find patients by name/phone
      ],
      openaiApiKey
    );
  }

  /**
   * Create execution plan based on analyzed intent
   */
  protected async planExecution(
    intent: any,
    context: ExecutionContext
  ): Promise<AgentPlan> {
    const { intent: intentDescription, entities, confidence } = intent;

    // Use GPT-4 to create a step-by-step plan
    const systemPrompt = `You are an AI planning assistant for the AppointmentAgent.

Your task is to create a step-by-step execution plan using available tools.

Available tools:
- appointment.check_availability: Check available slots (params: practitioner_id?, speciality?, date_start, date_end, location_id?, duration?)
- appointment.book: Book appointment (params: patient_id, practitioner_id, slot_id, appointment_type, notes?)
- appointment.cancel: Cancel appointment (params: appointment_id, reason?)
- appointment.reschedule: Reschedule appointment (params: appointment_id, new_slot_id, reason?)
- appointment.get: Get appointment details (params: appointment_id)
- patient.search: Search for patient (params: query, search_type?)

User intent: ${intentDescription}
Extracted entities: ${JSON.stringify(entities, null, 2)}

Create a JSON plan with:
- steps: Array of {toolName, params, reasoning}
- reasoning: Overall plan explanation
- requiresConfirmation: Boolean (true for booking, canceling, rescheduling)

IMPORTANT:
- If you need to find a patient, use patient.search first
- If booking, check availability first
- Always validate you have required parameters
- If missing critical info, create a plan with empty steps and explain what's missing in reasoning`;

    const completion = await this.openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        { role: 'system', content: systemPrompt },
        {
          role: 'user',
          content: `Create execution plan for this request.`,
        },
      ],
      response_format: { type: 'json_object' },
      temperature: 0.3,
    });

    const result = completion.choices[0].message.content;
    const plan = result ? JSON.parse(result) : { steps: [], reasoning: '', requiresConfirmation: false };

    return plan;
  }

  /**
   * Format tool execution results into human-readable response
   */
  protected async formatResponse(
    results: ToolResult[],
    intent: any
  ): Promise<string> {
    // Check if all steps succeeded
    const allSucceeded = results.every((r) => r.success);
    const lastResult = results[results.length - 1];

    if (!allSucceeded) {
      // Find the first failed step
      const failedResult = results.find((r) => !r.success);
      return `I encountered an error: ${failedResult?.error?.message || 'Unknown error occurred'}. ${this.getSuggestion(failedResult)}`;
    }

    // Use GPT-4 to format a natural, friendly response
    const systemPrompt = `You are a friendly healthcare assistant responding to a user after completing their request.

Create a natural, conversational response that:
1. Confirms what was done
2. Provides relevant details from the results
3. Is warm and professional
4. Is concise (2-3 sentences max)

Format dates nicely (e.g., "tomorrow at 2:00 PM" instead of ISO format).
Use natural language.`;

    const userPrompt = `User's original intent: ${intent.intent || intent}

Tool execution results:
${JSON.stringify(results.map((r) => ({ success: r.success, data: r.data })), null, 2)}

Create a friendly response message.`;

    const completion = await this.openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.7,
      max_tokens: 200,
    });

    return (
      completion.choices[0].message.content ||
      'Your request has been completed successfully.'
    );
  }

  /**
   * Provide helpful suggestions based on errors
   */
  private getSuggestion(failedResult?: ToolResult): string {
    if (!failedResult?.error) return '';

    const errorCode = failedResult.error.code;

    const suggestions: Record<string, string> = {
      PATIENT_NOT_FOUND: 'Please check the patient name or phone number.',
      AVAILABILITY_CHECK_FAILED: 'Try selecting a different date range.',
      BOOKING_FAILED:
        'The slot may no longer be available. Would you like to check for other times?',
      CANCELLATION_FAILED: 'Please verify the appointment ID.',
      RESCHEDULE_FAILED:
        'The new slot may not be available. Would you like to see other options?',
    };

    return suggestions[errorCode] || 'Please try again or contact support.';
  }

  /**
   * Check if this agent can handle the given intent
   */
  canHandle(intent: string): boolean {
    const appointmentKeywords = [
      'appointment',
      'schedule',
      'book',
      'cancel',
      'reschedule',
      'availability',
      'slot',
      'doctor',
      'practitioner',
      'consultation',
    ];

    const lowerIntent = intent.toLowerCase();
    return appointmentKeywords.some((keyword) => lowerIntent.includes(keyword));
  }

  /**
   * Get agent capabilities for display
   */
  getCapabilities() {
    return {
      name: 'AppointmentAgent',
      description:
        'Manages all appointment-related operations in the healthcare system',
      capabilities: [
        {
          name: 'Check Availability',
          description:
            'Find available appointment slots for practitioners or specialities',
          examples: [
            'Show me available slots for Dr. Smith next week',
            'When is cardiology available tomorrow?',
            'Check availability for orthopedics this Friday',
          ],
        },
        {
          name: 'Book Appointments',
          description: 'Schedule new appointments for patients',
          examples: [
            'Book an appointment for John Doe with Dr. Smith on Monday at 2pm',
            'Schedule a consultation for patient 12345 tomorrow',
            'Book a follow-up for Mary Johnson next week',
          ],
        },
        {
          name: 'Cancel Appointments',
          description: 'Cancel existing appointments',
          examples: [
            'Cancel appointment APT123',
            'Cancel John\'s appointment tomorrow',
            'Remove the 2pm appointment today',
          ],
        },
        {
          name: 'Reschedule Appointments',
          description: 'Move appointments to new time slots',
          examples: [
            'Reschedule appointment APT123 to Thursday at 3pm',
            'Move John\'s appointment to next Monday',
            'Change the 2pm slot to 4pm',
          ],
        },
        {
          name: 'View Appointment Details',
          description: 'Retrieve information about specific appointments',
          examples: [
            'Show me appointment APT123',
            'Get details for John\'s next appointment',
            'What\'s scheduled for tomorrow at 2pm?',
          ],
        },
      ],
      version: '1.0.0',
    };
  }
}
