import OpenAI from 'openai';
import { toolRegistry } from '../tools/registry';
import { ExecutionContext, ToolResult } from '../tools/types';

/**
 * Agent execution step
 */
export interface AgentStep {
  toolName: string;
  params: Record<string, any>;
  reasoning: string;
}

/**
 * Agent execution plan
 */
export interface AgentPlan {
  steps: AgentStep[];
  reasoning: string;
  requiresConfirmation: boolean;
}

/**
 * Agent execution result
 */
export interface AgentResult {
  success: boolean;
  message: string;
  data?: any;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    executionTime?: number;
    toolsUsed?: string[];
    stepsCompleted?: number;
    [key: string]: any;
  };
}

/**
 * BaseAgent
 * Abstract base class for all specialized agents
 * Provides core agent functionality: intent analysis, planning, execution
 */
export abstract class BaseAgent {
  protected openai: OpenAI;
  protected agentName: string;
  protected agentDescription: string;
  protected availableTools: string[];

  constructor(
    name: string,
    description: string,
    availableTools: string[],
    openaiApiKey?: string
  ) {
    this.agentName = name;
    this.agentDescription = description;
    this.availableTools = availableTools;

    // Initialize OpenAI client
    this.openai = new OpenAI({
      apiKey: openaiApiKey || process.env.OPENAI_API_KEY || '',
      dangerouslyAllowBrowser: true, // For client-side usage (consider moving to server-side)
    });
  }

  /**
   * Main entry point for agent execution
   * Orchestrates the entire agent workflow
   */
  async execute(
    userInput: string,
    context: ExecutionContext
  ): Promise<AgentResult> {
    const startTime = Date.now();
    const toolsUsed: string[] = [];

    try {
      // Step 1: Analyze user intent
      const intent = await this.analyzeIntent(userInput, context);

      // Step 2: Create execution plan
      const plan = await this.planExecution(intent, context);

      // Step 3: Check if confirmation is needed
      if (plan.requiresConfirmation) {
        return {
          success: true,
          message: 'Confirmation required before execution',
          data: {
            plan,
            intent,
            requiresConfirmation: true,
          },
          metadata: {
            executionTime: Date.now() - startTime,
            toolsUsed: [],
            stepsCompleted: 0,
          },
        };
      }

      // Step 4: Execute the plan
      const executionResults = await this.executePlan(plan, context);
      toolsUsed.push(...plan.steps.map((s) => s.toolName));

      // Step 5: Format response for user
      const response = await this.formatResponse(executionResults, intent);

      return {
        success: true,
        message: response,
        data: executionResults,
        metadata: {
          executionTime: Date.now() - startTime,
          toolsUsed,
          stepsCompleted: plan.steps.length,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        message: 'Agent execution failed',
        error: {
          code: 'AGENT_EXECUTION_ERROR',
          message: error.message || 'Unknown error occurred',
          details: error,
        },
        metadata: {
          executionTime: Date.now() - startTime,
          toolsUsed,
          stepsCompleted: 0,
        },
      };
    }
  }

  /**
   * Execute with confirmation (after user approves the plan)
   */
  async executeWithConfirmation(
    plan: AgentPlan,
    context: ExecutionContext
  ): Promise<AgentResult> {
    const startTime = Date.now();
    const toolsUsed = plan.steps.map((s) => s.toolName);

    try {
      // Execute the plan
      const executionResults = await this.executePlan(plan, context);

      // Format response
      const response = await this.formatResponse(
        executionResults,
        plan.reasoning
      );

      return {
        success: true,
        message: response,
        data: executionResults,
        metadata: {
          executionTime: Date.now() - startTime,
          toolsUsed,
          stepsCompleted: plan.steps.length,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        message: 'Agent execution failed',
        error: {
          code: 'AGENT_EXECUTION_ERROR',
          message: error.message || 'Unknown error occurred',
          details: error,
        },
        metadata: {
          executionTime: Date.now() - startTime,
          toolsUsed,
          stepsCompleted: 0,
        },
      };
    }
  }

  /**
   * Analyze user intent using LLM
   * Extracts structured information from natural language
   */
  protected async analyzeIntent(
    userInput: string,
    context: ExecutionContext
  ): Promise<any> {
    const systemPrompt = `You are ${this.agentName}, ${this.agentDescription}.

Your role is to analyze user requests and extract structured intent.

Available tools: ${this.availableTools.join(', ')}

Respond with a JSON object containing:
- intent: Brief description of what the user wants
- entities: Key information extracted from the request (names, dates, IDs, etc.)
- confidence: Your confidence level (0-1)
- clarifications: Array of questions if anything is unclear

Be precise and extract all relevant entities.`;

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
    return result ? JSON.parse(result) : {};
  }

  /**
   * Create execution plan
   * MUST be implemented by subclasses
   * Converts intent into concrete steps with tools
   */
  protected abstract planExecution(
    intent: any,
    context: ExecutionContext
  ): Promise<AgentPlan>;

  /**
   * Execute the plan step by step
   * Runs each tool in sequence, passing context between steps
   */
  protected async executePlan(
    plan: AgentPlan,
    context: ExecutionContext
  ): Promise<ToolResult[]> {
    const results: ToolResult[] = [];

    for (const step of plan.steps) {
      try {
        const result = await toolRegistry.executeTool(
          step.toolName,
          step.params,
          context
        );

        results.push(result);

        // If any step fails, stop execution
        if (!result.success) {
          break;
        }
      } catch (error: any) {
        results.push({
          success: false,
          error: {
            code: 'TOOL_EXECUTION_ERROR',
            message: error.message,
            details: error,
          },
        });
        break;
      }
    }

    return results;
  }

  /**
   * Format response for the user
   * MUST be implemented by subclasses
   * Converts tool results into human-readable response
   */
  protected abstract formatResponse(
    results: ToolResult[],
    intent: any
  ): Promise<string>;

  /**
   * Get available tools for this agent
   */
  getAvailableTools(): string[] {
    return this.availableTools;
  }

  /**
   * Get agent name
   */
  getName(): string {
    return this.agentName;
  }

  /**
   * Get agent description
   */
  getDescription(): string {
    return this.agentDescription;
  }

  /**
   * Check if agent can handle a given intent
   * Can be overridden by subclasses for custom logic
   */
  canHandle(intent: string): boolean {
    // Default implementation - can be overridden
    return true;
  }
}
