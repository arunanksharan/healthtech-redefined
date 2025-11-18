/**
 * Tool System Types
 * Tools are atomic operations that agents can execute
 */

/**
 * Parameter definition for a tool
 */
export interface ToolParameter {
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description: string;
  required: boolean;
  enum?: string[];
  default?: any;
}

/**
 * Tool parameters schema
 */
export type ToolParameters = Record<string, ToolParameter>;

/**
 * Execution context passed to all tools
 */
export interface ExecutionContext {
  userId: string;
  orgId: string;
  sessionId: string;
  requestId: string;
  permissions: string[];
}

/**
 * Result returned by tool execution
 */
export interface ToolResult {
  success: boolean;
  data?: any;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    executionTime?: number;
    cacheHit?: boolean;
    [key: string]: any;
  };
}

/**
 * Tool definition
 * A tool is an atomic operation that can be executed by an agent
 */
export interface Tool {
  name: string;
  description: string;
  parameters: ToolParameters;
  execute: (params: any, context: ExecutionContext) => Promise<ToolResult>;
  requiresConfirmation?: boolean;
  riskLevel?: 'low' | 'medium' | 'high';
}

/**
 * Tool execution request
 */
export interface ToolExecutionRequest {
  toolName: string;
  params: Record<string, any>;
  context: ExecutionContext;
}

/**
 * Tool category for organization
 */
export type ToolCategory =
  | 'appointment'
  | 'patient'
  | 'journey'
  | 'communication'
  | 'billing'
  | 'ticket'
  | 'search'
  | 'analytics';
