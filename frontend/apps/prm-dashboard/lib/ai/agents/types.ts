/**
 * Agent System Types
 * Types for the agent orchestration system
 */

import { ExecutionContext, ToolResult } from '../tools/types';
import { AgentPlan, AgentResult } from './BaseAgent';

/**
 * Agent capability definition
 */
export interface AgentCapability {
  name: string;
  description: string;
  examples: string[];
}

/**
 * Agent metadata
 */
export interface AgentMetadata {
  name: string;
  description: string;
  capabilities: AgentCapability[];
  version: string;
  author?: string;
}

/**
 * Agent interface
 * All agents must implement this interface
 */
export interface IAgent {
  execute(userInput: string, context: ExecutionContext): Promise<AgentResult>;
  executeWithConfirmation(
    plan: AgentPlan,
    context: ExecutionContext
  ): Promise<AgentResult>;
  getAvailableTools(): string[];
  getName(): string;
  getDescription(): string;
  canHandle(intent: string): boolean;
}

/**
 * Intent classification result
 */
export interface IntentClassification {
  agentName: string;
  confidence: number;
  intent: string;
  entities: Record<string, any>;
  requiresMultipleAgents: boolean;
  agentChain?: string[];
}

/**
 * Agent execution context (extended)
 */
export interface AgentExecutionContext extends ExecutionContext {
  conversationHistory?: ConversationMessage[];
  userPreferences?: Record<string, any>;
  agentChain?: string[];
}

/**
 * Conversation message
 */
export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    agentName?: string;
    toolsUsed?: string[];
    [key: string]: any;
  };
}

/**
 * Agent registry entry
 */
export interface AgentRegistryEntry {
  agent: IAgent;
  metadata: AgentMetadata;
  priority: number;
}

/**
 * Orchestrator result
 */
export interface OrchestratorResult {
  success: boolean;
  message: string;
  agentsUsed: string[];
  results: AgentResult[];
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    executionTime?: number;
    totalSteps?: number;
    [key: string]: any;
  };
}
