import { BaseAgent, AgentPlan, AgentResult } from './BaseAgent';
import { ExecutionContext, ToolResult } from '../tools/types';

/**
 * JourneyAgent
 * Specialized agent for managing care journeys
 *
 * Capabilities:
 * - Create new care journeys for patients
 * - Add steps to journeys
 * - Complete journey steps
 * - Update journey status
 * - Track journey progress
 * - List patient journeys
 */
export class JourneyAgent extends BaseAgent {
  constructor(openaiApiKey?: string) {
    super(
      'JourneyAgent',
      'an AI assistant specialized in managing care journeys and patient pathways',
      [
        'journey.get',
        'journey.create',
        'journey.add_step',
        'journey.complete_step',
        'journey.complete',
        'journey.list_for_patient',
        'journey.update',
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
    const systemPrompt = `You are an AI planning assistant for the JourneyAgent.

Your task is to create a step-by-step execution plan using available tools.

Available tools:
- journey.get: Get journey details (params: journey_id)
- journey.create: Create new journey (params: patient_id, journey_type, title, description?, template_id?)
  - journey_type: 'post_surgery' | 'chronic_disease' | 'wellness' | 'pregnancy' | 'other'
- journey.add_step: Add step to journey (params: journey_id, step_title, step_description?, step_type?, due_date?, assigned_to?)
  - step_type: 'appointment' | 'medication' | 'test' | 'follow_up' | 'task' | 'milestone'
- journey.complete_step: Complete a step (params: journey_id, step_id, notes?)
- journey.complete: Complete entire journey (params: journey_id, completion_notes?)
- journey.list_for_patient: List patient journeys (params: patient_id, status?)
  - status: 'active' | 'completed' | 'paused' | 'cancelled'
- journey.update: Update journey (params: journey_id, updates)
- patient.search: Search for patient (params: query, search_type?)

User intent: ${intentDescription}
Extracted entities: ${JSON.stringify(entities, null, 2)}

Create a JSON plan with:
- steps: Array of {toolName, params, reasoning}
- reasoning: Overall plan explanation
- requiresConfirmation: Boolean (true for creating, completing journeys)

IMPORTANT:
- If you need to find a patient, use patient.search first
- For creating journeys, always specify journey_type and title
- When adding steps, provide clear step_title
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
    const systemPrompt = `You are a friendly healthcare assistant responding to a user after completing a journey management request.

Create a natural, conversational response that:
1. Confirms what was done
2. Provides relevant details from the results
3. Is warm and professional
4. Is concise (2-3 sentences max)

For journey creation:
- Confirm the journey was created
- Mention the journey type and patient
- Provide next steps if relevant

For step management:
- Confirm the action (added step, completed step)
- Mention the step details
- Show progress if relevant

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
      JOURNEY_NOT_FOUND: 'Please check the journey ID.',
      JOURNEY_CREATE_FAILED: 'Please ensure the patient ID is valid and all required fields are provided.',
      STEP_ADD_FAILED: 'Please verify the journey ID and step details.',
      STEP_COMPLETE_FAILED: 'Please check the journey ID and step ID.',
      JOURNEY_COMPLETE_FAILED: 'Please verify the journey ID.',
      JOURNEYS_FETCH_FAILED: 'Please check the patient ID.',
    };

    return suggestions[errorCode] || 'Please try again or contact support.';
  }

  /**
   * Check if this agent can handle the given intent
   */
  canHandle(intent: string): boolean {
    const journeyKeywords = [
      'journey',
      'care journey',
      'pathway',
      'care plan',
      'treatment plan',
      'recovery',
      'step',
      'milestone',
      'complete journey',
      'create journey',
      'add step',
    ];

    const lowerIntent = intent.toLowerCase();
    return journeyKeywords.some((keyword) => lowerIntent.includes(keyword));
  }

  /**
   * Get agent capabilities for display
   */
  getCapabilities() {
    return {
      name: 'JourneyAgent',
      description: 'Manages care journeys and patient pathways',
      capabilities: [
        {
          name: 'Create Journey',
          description: 'Create new care journeys for patients',
          examples: [
            'Create a post-surgery recovery journey for patient John',
            'Start diabetes management journey for patient 123',
            'Create pregnancy care journey for Mary',
          ],
        },
        {
          name: 'Add Journey Steps',
          description: 'Add steps and milestones to existing journeys',
          examples: [
            'Add a follow-up appointment step to journey 456',
            'Add medication reminder to the recovery journey',
            'Add lab test step due next week',
          ],
        },
        {
          name: 'Complete Steps',
          description: 'Mark journey steps as completed',
          examples: [
            'Complete the first step of journey 789',
            'Mark lab test step as done',
            'Complete all pending steps for journey 123',
          ],
        },
        {
          name: 'View Journeys',
          description: 'View journey details and progress',
          examples: [
            'Show me journey 456',
            'List all active journeys for patient John',
            'Get journey progress for patient 123',
          ],
        },
        {
          name: 'Complete Journey',
          description: 'Mark entire journeys as completed',
          examples: [
            'Complete journey 789',
            'Mark post-surgery journey as finished',
            'Close the recovery pathway',
          ],
        },
        {
          name: 'Update Journey',
          description: 'Update journey information and status',
          examples: [
            'Pause journey 456',
            'Update journey description',
            'Change journey status to active',
          ],
        },
      ],
      version: '1.0.0',
    };
  }
}
