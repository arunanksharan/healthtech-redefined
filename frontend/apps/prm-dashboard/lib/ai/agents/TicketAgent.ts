import { BaseAgent, AgentPlan, AgentResult } from './BaseAgent';
import { ExecutionContext, ToolResult } from '../tools/types';

/**
 * TicketAgent
 * Specialized agent for managing support tickets
 *
 * Capabilities:
 * - Create support tickets
 * - Update ticket status
 * - Assign tickets to team members
 * - Resolve and close tickets
 * - Add comments to tickets
 * - Track ticket progress
 */
export class TicketAgent extends BaseAgent {
  constructor(openaiApiKey?: string) {
    super(
      'TicketAgent',
      'an AI assistant specialized in managing support tickets and issue tracking',
      [
        'ticket.create',
        'ticket.get',
        'ticket.update',
        'ticket.assign',
        'ticket.resolve',
        'ticket.close',
        'ticket.add_comment',
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
    const systemPrompt = `You are an AI planning assistant for the TicketAgent.

Your task is to create a step-by-step execution plan using available tools.

Available tools:
- ticket.create: Create new ticket (params: title, description, category, priority?, patient_id?, assigned_to?)
  - category: 'billing' | 'appointment' | 'medical' | 'technical' | 'general'
  - priority: 'low' | 'medium' | 'high' | 'urgent'
- ticket.get: Get ticket details (params: ticket_id)
- ticket.update: Update ticket (params: ticket_id, updates)
- ticket.assign: Assign to user (params: ticket_id, assigned_to)
- ticket.resolve: Resolve ticket (params: ticket_id, resolution_notes?)
- ticket.close: Close ticket (params: ticket_id)
- ticket.add_comment: Add comment (params: ticket_id, comment, is_internal?)
- patient.search: Search for patient (params: query, search_type?)

User intent: ${intentDescription}
Extracted entities: ${JSON.stringify(entities, null, 2)}

Create a JSON plan with:
- steps: Array of {toolName, params, reasoning}
- reasoning: Overall plan explanation
- requiresConfirmation: Boolean (false for most ticket operations)

IMPORTANT:
- If patient mentioned, use patient.search first
- Always include title and description when creating tickets
- Set appropriate category and priority
- For updates, use ticket.update with specific fields
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
    const systemPrompt = `You are a friendly support assistant responding to a user after completing a ticket management request.

Create a natural, conversational response that:
1. Confirms what was done
2. Provides relevant details from the results
3. Is warm and professional
4. Is concise (2-3 sentences max)

For ticket creation:
- Confirm the ticket was created
- Mention the ticket ID
- Provide next steps if relevant

For ticket updates:
- Confirm the action (assigned, resolved, closed)
- Mention ticket ID
- Highlight status change

Use natural language and be helpful.`;

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
      'Your ticket request has been completed successfully.'
    );
  }

  /**
   * Provide helpful suggestions based on errors
   */
  private getSuggestion(failedResult?: ToolResult): string {
    if (!failedResult?.error) return '';

    const errorCode = failedResult.error.code;

    const suggestions: Record<string, string> = {
      TICKET_NOT_FOUND: 'Please check the ticket ID.',
      TICKET_CREATE_FAILED: 'Please ensure all required fields are provided.',
      TICKET_UPDATE_FAILED: 'Please verify the ticket ID and update fields.',
      TICKET_ASSIGN_FAILED: 'Please check the user ID for assignment.',
      TICKET_RESOLVE_FAILED: 'Please verify the ticket can be resolved.',
      TICKET_CLOSE_FAILED: 'Please verify the ticket can be closed.',
      COMMENT_ADD_FAILED: 'Please check the ticket ID and comment text.',
    };

    return suggestions[errorCode] || 'Please try again or contact support.';
  }

  /**
   * Check if this agent can handle the given intent
   */
  canHandle(intent: string): boolean {
    const ticketKeywords = [
      'ticket',
      'issue',
      'problem',
      'support',
      'help',
      'complaint',
      'feedback',
      'bug',
      'request',
      'inquiry',
      'resolve',
      'assign',
      'close ticket',
      'create ticket',
    ];

    const lowerIntent = intent.toLowerCase();
    return ticketKeywords.some((keyword) => lowerIntent.includes(keyword));
  }

  /**
   * Get agent capabilities for display
   */
  getCapabilities() {
    return {
      name: 'TicketAgent',
      description: 'Manages support tickets and issue tracking',
      capabilities: [
        {
          name: 'Create Ticket',
          description: 'Create new support tickets',
          examples: [
            'Create ticket for billing issue with patient John',
            'Open support ticket about appointment scheduling problem',
            'Create urgent ticket for technical issue',
          ],
        },
        {
          name: 'Update Ticket',
          description: 'Update ticket information and status',
          examples: [
            'Update ticket TKT123 status to in progress',
            'Change priority of ticket 456 to high',
            'Update ticket description',
          ],
        },
        {
          name: 'Assign Ticket',
          description: 'Assign tickets to team members',
          examples: [
            'Assign ticket TKT123 to user 456',
            'Assign billing ticket to finance team',
            'Transfer ticket to support specialist',
          ],
        },
        {
          name: 'Resolve Ticket',
          description: 'Mark tickets as resolved',
          examples: [
            'Resolve ticket TKT123',
            'Mark ticket 456 as resolved with solution notes',
            'Close and resolve the billing ticket',
          ],
        },
        {
          name: 'Add Comments',
          description: 'Add comments and notes to tickets',
          examples: [
            'Add comment to ticket TKT123 about follow-up',
            'Add internal note to ticket 456',
            'Comment on ticket with status update',
          ],
        },
        {
          name: 'Track Tickets',
          description: 'View and track ticket progress',
          examples: [
            'Show me ticket TKT123',
            'Get details for ticket 456',
            'What\'s the status of the billing ticket?',
          ],
        },
      ],
      version: '1.0.0',
    };
  }
}
