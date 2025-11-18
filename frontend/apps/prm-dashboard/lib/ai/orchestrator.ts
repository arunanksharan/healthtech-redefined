import { agentRegistry } from './agents/registry';
import { intentParser } from './intent-parser';
import {
  OrchestratorResult,
  AgentExecutionContext,
  ConversationMessage,
} from './agents/types';
import { AgentResult } from './agents/BaseAgent';

/**
 * Orchestrator
 * Main entry point for the AI system
 * Coordinates intent parsing, agent selection, and execution
 */
export class Orchestrator {
  private conversationHistory: Map<string, ConversationMessage[]> = new Map();

  /**
   * Process user input and orchestrate agent execution
   */
  async process(
    userInput: string,
    context: AgentExecutionContext
  ): Promise<OrchestratorResult> {
    const startTime = Date.now();
    const agentsUsed: string[] = [];
    const results: AgentResult[] = [];

    try {
      // Step 1: Parse intent
      const classification = await intentParser.parseIntent(userInput);

      // Validate classification
      if (!intentParser.validateClassification(classification)) {
        return {
          success: false,
          message: 'Unable to process request',
          agentsUsed: [],
          results: [],
          error: {
            code: 'INVALID_CLASSIFICATION',
            message: 'Intent classification failed validation',
          },
        };
      }

      // Step 2: Handle low confidence - request clarification
      if (classification.confidence < 0.7) {
        const clarifications =
          await intentParser.getSuggestedClarifications(
            userInput,
            classification
          );

        return {
          success: true,
          message: 'I need some clarification to help you better.',
          agentsUsed: [],
          results: [],
          metadata: {
            requiresClarification: true,
            clarifications,
            classification,
          },
        };
      }

      // Step 3: Add to conversation history
      this.addToHistory(context.sessionId, {
        role: 'user',
        content: userInput,
        timestamp: new Date(),
      });

      // Update context with conversation history
      const enrichedContext: AgentExecutionContext = {
        ...context,
        conversationHistory: this.getHistory(context.sessionId),
      };

      // Step 4: Execute with single agent or multi-agent chain
      if (classification.requiresMultipleAgents && classification.agentChain) {
        // Multi-agent execution
        const chainResults = await this.executeAgentChain(
          classification.agentChain,
          userInput,
          enrichedContext
        );

        agentsUsed.push(...classification.agentChain);
        results.push(...chainResults);
      } else {
        // Single agent execution
        const agent = agentRegistry.getAgent(classification.agentName);

        if (!agent) {
          return {
            success: false,
            message: `Agent ${classification.agentName} not found`,
            agentsUsed: [],
            results: [],
            error: {
              code: 'AGENT_NOT_FOUND',
              message: `Agent ${classification.agentName} not found`,
            },
          };
        }

        const result = await agent.execute(userInput, enrichedContext);

        agentsUsed.push(classification.agentName);
        results.push(result);
      }

      // Step 5: Check if all results succeeded
      const allSucceeded = results.every((r) => r.success);
      const finalResult = results[results.length - 1];

      // Step 6: Add assistant response to history
      this.addToHistory(context.sessionId, {
        role: 'assistant',
        content: finalResult.message,
        timestamp: new Date(),
        metadata: {
          agentName: agentsUsed[agentsUsed.length - 1],
          toolsUsed: finalResult.metadata?.toolsUsed,
        },
      });

      // Step 7: Return orchestrator result
      return {
        success: allSucceeded,
        message: finalResult.message,
        agentsUsed,
        results,
        metadata: {
          executionTime: Date.now() - startTime,
          totalSteps: results.reduce(
            (sum, r) => sum + (r.metadata?.stepsCompleted || 0),
            0
          ),
          classification,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        message: 'An error occurred while processing your request',
        agentsUsed,
        results,
        error: {
          code: 'ORCHESTRATION_ERROR',
          message: error.message || 'Unknown error occurred',
          details: error,
        },
        metadata: {
          executionTime: Date.now() - startTime,
        },
      };
    }
  }

  /**
   * Execute a chain of agents in sequence
   */
  private async executeAgentChain(
    agentChain: string[],
    userInput: string,
    context: AgentExecutionContext
  ): Promise<AgentResult[]> {
    const results: AgentResult[] = [];
    let currentInput = userInput;

    for (const agentName of agentChain) {
      const agent = agentRegistry.getAgent(agentName);

      if (!agent) {
        results.push({
          success: false,
          message: `Agent ${agentName} not found`,
          error: {
            code: 'AGENT_NOT_FOUND',
            message: `Agent ${agentName} not found in chain`,
          },
        });
        break;
      }

      // Execute agent
      const result = await agent.execute(currentInput, {
        ...context,
        agentChain,
      });

      results.push(result);

      // If agent failed, stop the chain
      if (!result.success) {
        break;
      }

      // Use the result data as context for the next agent
      // This allows agents to pass information down the chain
      if (result.data) {
        currentInput = `${userInput}\n\nContext from previous agent: ${JSON.stringify(result.data)}`;
      }
    }

    return results;
  }

  /**
   * Add message to conversation history
   */
  private addToHistory(sessionId: string, message: ConversationMessage): void {
    if (!this.conversationHistory.has(sessionId)) {
      this.conversationHistory.set(sessionId, []);
    }

    const history = this.conversationHistory.get(sessionId)!;
    history.push(message);

    // Keep only last 50 messages per session
    if (history.length > 50) {
      history.shift();
    }
  }

  /**
   * Get conversation history for a session
   */
  getHistory(sessionId: string): ConversationMessage[] {
    return this.conversationHistory.get(sessionId) || [];
  }

  /**
   * Clear conversation history for a session
   */
  clearHistory(sessionId: string): void {
    this.conversationHistory.delete(sessionId);
  }

  /**
   * Get all active sessions
   */
  getActiveSessions(): string[] {
    return Array.from(this.conversationHistory.keys());
  }

  /**
   * Get conversation summary for a session
   */
  getConversationSummary(sessionId: string): {
    messageCount: number;
    userMessages: number;
    assistantMessages: number;
    lastMessage?: ConversationMessage;
  } {
    const history = this.getHistory(sessionId);

    return {
      messageCount: history.length,
      userMessages: history.filter((m) => m.role === 'user').length,
      assistantMessages: history.filter((m) => m.role === 'assistant').length,
      lastMessage: history[history.length - 1],
    };
  }
}

// Singleton instance
export const orchestrator = new Orchestrator();
