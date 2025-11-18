import { BaseAgent, AgentPlan, AgentResult } from './BaseAgent';
import { ExecutionContext, ToolResult } from '../tools/types';

/**
 * PatientAgent
 * Specialized agent for handling all patient-related operations
 *
 * Capabilities:
 * - Search for patients
 * - View patient details
 * - Get patient 360° view
 * - Create new patient records
 * - Update patient information
 */
export class PatientAgent extends BaseAgent {
  constructor(openaiApiKey?: string) {
    super(
      'PatientAgent',
      'an AI assistant specialized in managing patient records and information',
      [
        'patient.search',
        'patient.get',
        'patient.get_360_view',
        'patient.create',
        'patient.update',
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
    const systemPrompt = `You are an AI planning assistant for the PatientAgent.

Your task is to create a step-by-step execution plan using available tools.

Available tools:
- patient.search: Search for patients (params: query, search_type?)
  - search_type can be: 'phone', 'name', 'mrn'
- patient.get: Get patient by ID (params: patient_id)
- patient.get_360_view: Get complete patient view (params: patient_id)
- patient.create: Create new patient (params: name, phone, email?, date_of_birth?, gender?)
- patient.update: Update patient info (params: patient_id, updates)

User intent: ${intentDescription}
Extracted entities: ${JSON.stringify(entities, null, 2)}

Create a JSON plan with:
- steps: Array of {toolName, params, reasoning}
- reasoning: Overall plan explanation
- requiresConfirmation: Boolean (true for create/update operations)

IMPORTANT:
- For searching, infer search_type from the query (phone numbers vs names)
- For 360° view requests, use patient.get_360_view
- For simple lookups, use patient.get
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

    if (!allSucceeded) {
      // Find the first failed step
      const failedResult = results.find((r) => !r.success);
      return `I encountered an error: ${failedResult?.error?.message || 'Unknown error occurred'}. ${this.getSuggestion(failedResult)}`;
    }

    // Use GPT-4 to format a natural, friendly response
    const systemPrompt = `You are a friendly healthcare assistant responding to a user after completing their patient-related request.

Create a natural, conversational response that:
1. Confirms what was done
2. Provides relevant details from the results
3. Is warm and professional
4. Is concise but informative

For search results:
- If multiple patients found, list them clearly
- If one patient found, provide key details (name, MRN, phone)
- If no patients found, say so clearly

For patient details:
- Highlight key information
- Format dates nicely
- Be respectful of patient privacy

For create/update operations:
- Confirm the action
- Provide the key details that changed`;

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
      max_tokens: 300,
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
      SEARCH_FAILED:
        'Try searching with a different term (name, phone, or MRN).',
      PATIENT_NOT_FOUND:
        'Double-check the patient ID or try searching by name/phone.',
      PATIENT_CREATE_ERROR:
        'Please ensure all required fields are provided (name and phone).',
      PATIENT_UPDATE_ERROR:
        'Please verify the patient ID and the fields you want to update.',
      '360_VIEW_ERROR':
        'There may be an issue retrieving the complete patient data.',
    };

    return suggestions[errorCode] || 'Please try again or contact support.';
  }

  /**
   * Check if this agent can handle the given intent
   */
  canHandle(intent: string): boolean {
    const patientKeywords = [
      'patient',
      'search',
      'find',
      'lookup',
      'create patient',
      'add patient',
      'update patient',
      'patient details',
      'patient info',
      '360',
      'complete view',
      'patient record',
    ];

    const lowerIntent = intent.toLowerCase();
    return patientKeywords.some((keyword) => lowerIntent.includes(keyword));
  }

  /**
   * Get agent capabilities for display
   */
  getCapabilities() {
    return {
      name: 'PatientAgent',
      description: 'Manages all patient-related data and operations',
      capabilities: [
        {
          name: 'Search Patients',
          description: 'Find patients by name, phone number, or MRN',
          examples: [
            'Search for patient John Doe',
            'Find patient with phone 9844111173',
            'Look up patient MRN12345',
          ],
        },
        {
          name: 'View Patient Details',
          description: 'Retrieve detailed information about a patient',
          examples: [
            'Show me details for patient ID 123',
            'Get info for John Doe',
            'Patient details for MRN12345',
          ],
        },
        {
          name: 'Patient 360° View',
          description:
            'Get complete patient view including appointments, journeys, and communications',
          examples: [
            'Show me complete view for patient 123',
            '360 view for John Doe',
            'Get all information for patient with phone 9844111173',
          ],
        },
        {
          name: 'Create Patient',
          description: 'Add new patient records to the system',
          examples: [
            'Create patient John Doe with phone 9844111173',
            'Add new patient Mary Smith, DOB 1990-01-15',
            'Register patient with email john@example.com',
          ],
        },
        {
          name: 'Update Patient',
          description: 'Modify existing patient information',
          examples: [
            'Update patient 123 email to newemail@example.com',
            'Change phone number for John Doe to 9876543210',
            'Update patient address',
          ],
        },
      ],
      version: '1.0.0',
    };
  }
}
