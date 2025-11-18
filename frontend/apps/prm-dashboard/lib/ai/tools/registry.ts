import { Tool, ToolResult, ExecutionContext, ToolCategory } from './types';

/**
 * Tool Registry
 * Central registry for all available tools
 * Manages registration, lookup, and execution of tools
 */
class ToolRegistry {
  private tools: Map<string, Tool> = new Map();
  private categories: Map<ToolCategory, Set<string>> = new Map();

  /**
   * Register a single tool
   */
  registerTool(tool: Tool, category?: ToolCategory): void {
    this.tools.set(tool.name, tool);

    // Add to category if provided
    if (category) {
      if (!this.categories.has(category)) {
        this.categories.set(category, new Set());
      }
      this.categories.get(category)?.add(tool.name);
    }
  }

  /**
   * Register multiple tools at once
   */
  registerTools(tools: Tool[], category?: ToolCategory): void {
    tools.forEach((tool) => this.registerTool(tool, category));
  }

  /**
   * Get a tool by name
   */
  getTool(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  /**
   * Get all registered tools
   */
  getAllTools(): Tool[] {
    return Array.from(this.tools.values());
  }

  /**
   * Get tools by category
   */
  getToolsByCategory(category: ToolCategory): Tool[] {
    const toolNames = this.categories.get(category);
    if (!toolNames) return [];

    return Array.from(toolNames)
      .map((name) => this.tools.get(name))
      .filter((tool): tool is Tool => tool !== undefined);
  }

  /**
   * Search tools by name or description
   */
  searchTools(query: string): Tool[] {
    const lowerQuery = query.toLowerCase();
    return this.getAllTools().filter(
      (tool) =>
        tool.name.toLowerCase().includes(lowerQuery) ||
        tool.description.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Execute a tool with error handling
   */
  async executeTool(
    toolName: string,
    params: any,
    context: ExecutionContext
  ): Promise<ToolResult> {
    const tool = this.getTool(toolName);

    if (!tool) {
      return {
        success: false,
        error: {
          code: 'TOOL_NOT_FOUND',
          message: `Tool "${toolName}" not found in registry`,
        },
      };
    }

    try {
      const startTime = Date.now();
      const result = await tool.execute(params, context);
      const executionTime = Date.now() - startTime;

      return {
        ...result,
        metadata: {
          ...result.metadata,
          executionTime,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        error: {
          code: 'TOOL_EXECUTION_ERROR',
          message: error.message || 'Tool execution failed',
          details: error,
        },
      };
    }
  }

  /**
   * Validate tool parameters before execution
   */
  validateParams(toolName: string, params: any): { valid: boolean; errors: string[] } {
    const tool = this.getTool(toolName);
    if (!tool) {
      return { valid: false, errors: ['Tool not found'] };
    }

    const errors: string[] = [];

    // Check required parameters
    for (const [paramName, paramDef] of Object.entries(tool.parameters)) {
      if (paramDef.required && !(paramName in params)) {
        errors.push(`Missing required parameter: ${paramName}`);
      }

      // Type validation
      if (paramName in params) {
        const value = params[paramName];
        const expectedType = paramDef.type;

        if (expectedType === 'string' && typeof value !== 'string') {
          errors.push(`Parameter ${paramName} must be a string`);
        } else if (expectedType === 'number' && typeof value !== 'number') {
          errors.push(`Parameter ${paramName} must be a number`);
        } else if (expectedType === 'boolean' && typeof value !== 'boolean') {
          errors.push(`Parameter ${paramName} must be a boolean`);
        } else if (expectedType === 'array' && !Array.isArray(value)) {
          errors.push(`Parameter ${paramName} must be an array`);
        } else if (
          expectedType === 'object' &&
          (typeof value !== 'object' || Array.isArray(value))
        ) {
          errors.push(`Parameter ${paramName} must be an object`);
        }

        // Enum validation
        if (paramDef.enum && !paramDef.enum.includes(value)) {
          errors.push(
            `Parameter ${paramName} must be one of: ${paramDef.enum.join(', ')}`
          );
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Get tool count
   */
  getToolCount(): number {
    return this.tools.size;
  }

  /**
   * Get category count
   */
  getCategoryCount(): number {
    return this.categories.size;
  }

  /**
   * Get all categories
   */
  getAllCategories(): ToolCategory[] {
    return Array.from(this.categories.keys());
  }
}

// Singleton instance
export const toolRegistry = new ToolRegistry();

// Export class for testing
export { ToolRegistry };
