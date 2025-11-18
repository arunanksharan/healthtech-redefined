import { BaseAgent, AgentPlan, AgentResult } from './BaseAgent';
import { ExecutionContext, ToolResult } from '../tools/types';

/**
 * CommunicationAgent
 * Specialized agent for managing patient communications
 *
 * Capabilities:
 * - Send WhatsApp messages
 * - Send SMS messages
 * - Send emails
 * - Bulk communications
 * - View communication history
 * - Manage templates
 */
export class CommunicationAgent extends BaseAgent {
  constructor(openaiApiKey?: string) {
    super(
      'CommunicationAgent',
      'an AI assistant specialized in managing patient communications via WhatsApp, SMS, and Email',
      [
        'communication.send_whatsapp',
        'communication.send_sms',
        'communication.send_email',
        'communication.send_bulk',
        'communication.get_templates',
        'communication.get_history',
        'patient.search', // Needed to find patients
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
    const systemPrompt = `You are an AI planning assistant for the CommunicationAgent.

Your task is to create a step-by-step execution plan using available tools.

Available tools:
- communication.send_whatsapp: Send WhatsApp (params: patient_id, message, template_id?, template_params?)
- communication.send_sms: Send SMS (params: patient_id, message, phone_number?)
- communication.send_email: Send Email (params: patient_id, subject, body, email_address?, template_id?)
- communication.send_bulk: Bulk send (params: patient_ids[], channel, message, subject?)
  - channel: 'whatsapp' | 'sms' | 'email'
- communication.get_templates: Get templates (params: channel?, category?)
  - channel: 'whatsapp' | 'sms' | 'email'
  - category: 'appointment' | 'reminder' | 'follow_up' | 'notification' | 'marketing'
- communication.get_history: Get history (params: patient_id, channel?, limit?)
- patient.search: Search for patient (params: query, search_type?)

User intent: ${intentDescription}
Extracted entities: ${JSON.stringify(entities, null, 2)}

Create a JSON plan with:
- steps: Array of {toolName, params, reasoning}
- reasoning: Overall plan explanation
- requiresConfirmation: Boolean (true for sending messages - always confirm before sending!)

IMPORTANT:
- If you need to find a patient, use patient.search first
- Always confirm before sending any communication
- For bulk sends, requiresConfirmation should be true (high risk)
- Extract message content, subject, channel type from user intent
- If using templates, get templates first to find the right one
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
    const systemPrompt = `You are a friendly healthcare assistant responding to a user after completing a communication request.

Create a natural, conversational response that:
1. Confirms what was done
2. Provides relevant details from the results
3. Is warm and professional
4. Is concise (2-3 sentences max)

For message sending:
- Confirm the message was sent
- Mention the channel (WhatsApp, SMS, Email)
- Confirm recipient(s)

For bulk communications:
- Confirm number of messages sent
- Mention the channel
- Highlight any failures if present

For templates/history:
- Summarize what was found
- Provide relevant counts

Use natural language and be encouraging.`;

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
      'Your communication has been sent successfully.'
    );
  }

  /**
   * Provide helpful suggestions based on errors
   */
  private getSuggestion(failedResult?: ToolResult): string {
    if (!failedResult?.error) return '';

    const errorCode = failedResult.error.code;

    const suggestions: Record<string, string> = {
      WHATSAPP_SEND_FAILED: 'Please check if the patient has a valid WhatsApp number.',
      SMS_SEND_FAILED: 'Please verify the patient phone number.',
      EMAIL_SEND_FAILED: 'Please check if the patient has a valid email address.',
      BULK_SEND_FAILED: 'Some messages may not have been sent. Please review patient contact information.',
      TEMPLATES_FETCH_FAILED: 'Unable to load templates. Please try again.',
      HISTORY_FETCH_FAILED: 'Unable to load communication history. Please verify the patient ID.',
    };

    return suggestions[errorCode] || 'Please try again or contact support.';
  }

  /**
   * Check if this agent can handle the given intent
   */
  canHandle(intent: string): boolean {
    const communicationKeywords = [
      'send',
      'message',
      'whatsapp',
      'sms',
      'email',
      'text',
      'notify',
      'remind',
      'communication',
      'template',
      'bulk',
      'broadcast',
    ];

    const lowerIntent = intent.toLowerCase();
    return communicationKeywords.some((keyword) => lowerIntent.includes(keyword));
  }

  /**
   * Get agent capabilities for display
   */
  getCapabilities() {
    return {
      name: 'CommunicationAgent',
      description: 'Manages patient communications via WhatsApp, SMS, and Email',
      capabilities: [
        {
          name: 'Send WhatsApp',
          description: 'Send WhatsApp messages to patients',
          examples: [
            'Send WhatsApp to patient John: Your appointment is tomorrow',
            'WhatsApp patient 123 their lab results are ready',
            'Send appointment reminder via WhatsApp to Mary',
          ],
        },
        {
          name: 'Send SMS',
          description: 'Send SMS messages to patients',
          examples: [
            'Send SMS to patient with phone 9844111173',
            'Text John about his follow-up appointment',
            'SMS reminder to patient 456',
          ],
        },
        {
          name: 'Send Email',
          description: 'Send emails to patients',
          examples: [
            'Email patient John the test results',
            'Send appointment confirmation email to Mary',
            'Email patient 789 about their medication',
          ],
        },
        {
          name: 'Bulk Communications',
          description: 'Send messages to multiple patients at once',
          examples: [
            'Send WhatsApp to all patients with appointments today',
            'Bulk SMS reminder to patients 123, 456, 789',
            'Email newsletter to all active patients',
          ],
        },
        {
          name: 'View Templates',
          description: 'Browse communication templates',
          examples: [
            'Show me appointment reminder templates',
            'List WhatsApp templates',
            'Get all email templates',
          ],
        },
        {
          name: 'Communication History',
          description: 'View past communications with patients',
          examples: [
            'Show communication history for patient John',
            'List all WhatsApp messages to patient 123',
            'Get email history for patient Mary',
          ],
        },
      ],
      version: '1.0.0',
    };
  }
}
