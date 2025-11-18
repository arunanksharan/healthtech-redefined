import OpenAI from 'openai';
import { agentRegistry } from './agents/registry';
import { IntentClassification } from './agents/types';

/**
 * IntentParser
 * Uses GPT-4 to classify user intents and route to appropriate agents
 */
export class IntentParser {
  private openai: OpenAI;

  constructor(openaiApiKey?: string) {
    this.openai = new OpenAI({
      apiKey: openaiApiKey || process.env.OPENAI_API_KEY || '',
      dangerouslyAllowBrowser: true,
    });
  }

  /**
   * Parse user input and classify intent
   */
  async parseIntent(userInput: string): Promise<IntentClassification> {
    try {
      // Get all available agents and their capabilities
      const allCapabilities = agentRegistry.getAllCapabilities();

      // Build context for GPT-4
      const systemPrompt = this.buildSystemPrompt(allCapabilities);

      // Call GPT-4 to classify intent
      const completion = await this.openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userInput },
        ],
        response_format: { type: 'json_object' },
        temperature: 0.3,
      });

      const result = completion.choices[0].message.content;
      const classification = result ? JSON.parse(result) : this.getDefaultClassification();

      return classification;
    } catch (error: any) {
      console.error('Intent parsing failed:', error);
      return this.getDefaultClassification();
    }
  }

  /**
   * Build system prompt with all agent capabilities
   */
  private buildSystemPrompt(
    allCapabilities: Array<{
      agentName: string;
      capabilities: any[];
    }>
  ): string {
    const agentDescriptions = allCapabilities
      .map((agent) => {
        const capabilities = agent.capabilities
          .map(
            (cap) =>
              `  - ${cap.name}: ${cap.description}\n    Examples: ${cap.examples.join(', ')}`
          )
          .join('\n');

        return `${agent.agentName}:\n${capabilities}`;
      })
      .join('\n\n');

    return `You are an intent classification system for a healthcare PRM (Patient Relationship Management) platform.

Your task is to analyze user requests and determine which agent should handle them.

Available agents and their capabilities:

${agentDescriptions}

Analyze the user's request and respond with a JSON object:

{
  "agentName": "AppointmentAgent" | "PatientAgent" | etc.,
  "confidence": 0.0 to 1.0,
  "intent": "Brief description of what the user wants",
  "entities": {
    // Key information extracted (names, dates, IDs, phone numbers, etc.)
  },
  "requiresMultipleAgents": false,
  "agentChain": [] // Array of agent names if multiple agents needed, in order
}

Rules:
1. Choose the MOST appropriate agent based on the primary intent
2. Extract all relevant entities (patient names/IDs, dates, phone numbers, etc.)
3. Set requiresMultipleAgents to true if the task requires coordination between multiple agents
4. If multiple agents needed, list them in agentChain in execution order
5. Confidence should reflect how clear the intent is (unclear/ambiguous = lower confidence)
6. If the request is unclear or you're unsure, set confidence below 0.7

Examples:

"Schedule a callback for patient John tomorrow at 2pm"
→ agentName: "AppointmentAgent", confidence: 0.95

"Find patient with phone 9844111173"
→ agentName: "PatientAgent", confidence: 0.98

"Book John for cardiology consultation next week"
→ agentName: "AppointmentAgent", confidence: 0.85, requiresMultipleAgents: true, agentChain: ["PatientAgent", "AppointmentAgent"]
  (Need to find patient first, then book appointment)`;
  }

  /**
   * Default classification when parsing fails
   */
  private getDefaultClassification(): IntentClassification {
    return {
      agentName: 'AppointmentAgent', // Default to appointment agent
      confidence: 0.5,
      intent: 'Unable to clearly determine intent',
      entities: {},
      requiresMultipleAgents: false,
    };
  }

  /**
   * Validate classification result
   */
  validateClassification(classification: IntentClassification): boolean {
    // Check if the specified agent exists
    if (!agentRegistry.hasAgent(classification.agentName)) {
      return false;
    }

    // Check if confidence is within valid range
    if (classification.confidence < 0 || classification.confidence > 1) {
      return false;
    }

    // Check if agentChain agents exist (if specified)
    if (classification.agentChain) {
      for (const agentName of classification.agentChain) {
        if (!agentRegistry.hasAgent(agentName)) {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * Get suggested clarifications when confidence is low
   */
  async getSuggestedClarifications(
    userInput: string,
    classification: IntentClassification
  ): Promise<string[]> {
    if (classification.confidence >= 0.7) {
      return []; // No clarifications needed
    }

    try {
      const systemPrompt = `You are a helpful assistant that identifies what information is missing or unclear in a user's request.

The user made a request, but it's unclear or missing information.

Intent classification:
- Agent: ${classification.agentName}
- Intent: ${classification.intent}
- Confidence: ${classification.confidence}
- Entities: ${JSON.stringify(classification.entities)}

Generate 2-4 clarifying questions to ask the user.

Respond with JSON:
{
  "questions": ["Question 1?", "Question 2?", ...]
}`;

      const completion = await this.openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userInput },
        ],
        response_format: { type: 'json_object' },
        temperature: 0.5,
      });

      const result = completion.choices[0].message.content;
      const parsed = result ? JSON.parse(result) : { questions: [] };

      return parsed.questions || [];
    } catch (error) {
      return ['Could you please provide more details?'];
    }
  }
}

// Singleton instance
export const intentParser = new IntentParser();
