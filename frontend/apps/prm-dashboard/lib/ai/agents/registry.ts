import { IAgent, AgentMetadata, AgentRegistryEntry } from './types';
import { AgentResult } from './BaseAgent';
import { ExecutionContext } from '../tools/types';

/**
 * AgentRegistry
 * Central registry for all available agents
 * Manages registration, lookup, and execution routing
 */
class AgentRegistry {
  private agents: Map<string, AgentRegistryEntry> = new Map();

  /**
   * Register a single agent
   */
  registerAgent(
    agent: IAgent,
    metadata: AgentMetadata,
    priority: number = 0
  ): void {
    this.agents.set(agent.getName(), {
      agent,
      metadata,
      priority,
    });
  }

  /**
   * Register multiple agents at once
   */
  registerAgents(
    entries: Array<{ agent: IAgent; metadata: AgentMetadata; priority?: number }>
  ): void {
    entries.forEach(({ agent, metadata, priority = 0 }) => {
      this.registerAgent(agent, metadata, priority);
    });
  }

  /**
   * Get an agent by name
   */
  getAgent(name: string): IAgent | undefined {
    return this.agents.get(name)?.agent;
  }

  /**
   * Get all registered agents
   */
  getAllAgents(): IAgent[] {
    return Array.from(this.agents.values())
      .sort((a, b) => b.priority - a.priority)
      .map((entry) => entry.agent);
  }

  /**
   * Get agent metadata
   */
  getAgentMetadata(name: string): AgentMetadata | undefined {
    return this.agents.get(name)?.metadata;
  }

  /**
   * Get all agent metadata
   */
  getAllMetadata(): AgentMetadata[] {
    return Array.from(this.agents.values()).map((entry) => entry.metadata);
  }

  /**
   * Find agents that can handle a given intent
   */
  findCapableAgents(intent: string): IAgent[] {
    return this.getAllAgents().filter((agent) => agent.canHandle(intent));
  }

  /**
   * Execute an agent by name
   */
  async executeAgent(
    agentName: string,
    userInput: string,
    context: ExecutionContext
  ): Promise<AgentResult> {
    const agent = this.getAgent(agentName);

    if (!agent) {
      return {
        success: false,
        message: `Agent "${agentName}" not found in registry`,
        error: {
          code: 'AGENT_NOT_FOUND',
          message: `Agent "${agentName}" not found in registry`,
        },
      };
    }

    try {
      const startTime = Date.now();
      const result = await agent.execute(userInput, context);
      const executionTime = Date.now() - startTime;

      return {
        ...result,
        metadata: {
          ...result.metadata,
          agentName,
          totalExecutionTime: executionTime,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        message: 'Agent execution failed',
        error: {
          code: 'AGENT_EXECUTION_ERROR',
          message: error.message || 'Agent execution failed',
          details: error,
        },
      };
    }
  }

  /**
   * Get agent count
   */
  getAgentCount(): number {
    return this.agents.size;
  }

  /**
   * Check if an agent exists
   */
  hasAgent(name: string): boolean {
    return this.agents.has(name);
  }

  /**
   * Get agents sorted by priority
   */
  getAgentsByPriority(): IAgent[] {
    return Array.from(this.agents.values())
      .sort((a, b) => b.priority - a.priority)
      .map((entry) => entry.agent);
  }

  /**
   * Search agents by capability
   */
  searchByCapability(query: string): IAgent[] {
    const lowerQuery = query.toLowerCase();

    return Array.from(this.agents.values())
      .filter((entry) => {
        const metadata = entry.metadata;

        // Search in agent description
        if (metadata.description.toLowerCase().includes(lowerQuery)) {
          return true;
        }

        // Search in capabilities
        return metadata.capabilities.some(
          (cap) =>
            cap.name.toLowerCase().includes(lowerQuery) ||
            cap.description.toLowerCase().includes(lowerQuery) ||
            cap.examples.some((ex) => ex.toLowerCase().includes(lowerQuery))
        );
      })
      .map((entry) => entry.agent);
  }

  /**
   * Get all capabilities across all agents
   */
  getAllCapabilities(): Array<{
    agentName: string;
    capabilities: AgentMetadata['capabilities'];
  }> {
    return Array.from(this.agents.values()).map((entry) => ({
      agentName: entry.agent.getName(),
      capabilities: entry.metadata.capabilities,
    }));
  }

  /**
   * Clear all agents (useful for testing)
   */
  clear(): void {
    this.agents.clear();
  }
}

// Singleton instance
export const agentRegistry = new AgentRegistry();

// Export class for testing
export { AgentRegistry };
