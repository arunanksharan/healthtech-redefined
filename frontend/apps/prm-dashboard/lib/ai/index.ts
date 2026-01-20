/**
 * AI System - Main Entry Point
 * Initializes and exports the complete AI system
 */

// Tools
import { toolRegistry } from './tools/registry';
import { appointmentTools } from './tools/appointment-tools';
import { patientTools } from './tools/patient-tools';
import { journeyTools } from './tools/journey-tools';
import { communicationTools } from './tools/communication-tools';
import { ticketTools } from './tools/ticket-tools';

// Agents
import { agentRegistry } from './agents/registry';
import { AppointmentAgent } from './agents/AppointmentAgent';
import { PatientAgent } from './agents/PatientAgent';
import { JourneyAgent } from './agents/JourneyAgent';
import { CommunicationAgent } from './agents/CommunicationAgent';
import { TicketAgent } from './agents/TicketAgent';

// Orchestrator
import { orchestrator } from './orchestrator';
import { intentParser } from './intent-parser';

// Types
export * from './tools/types';
export * from './agents/types';
export * from './agents/BaseAgent';

/**
 * Initialize the AI system
 * Registers all tools and agents
 */
export function initializeAISystem(openaiApiKey?: string): void {
  // Register all tools
  toolRegistry.registerTools(appointmentTools, 'appointment');
  toolRegistry.registerTools(patientTools, 'patient');
  toolRegistry.registerTools(journeyTools, 'journey');
  toolRegistry.registerTools(communicationTools, 'communication');
  toolRegistry.registerTools(ticketTools, 'ticket');

  // Create and register agents
  const appointmentAgent = new AppointmentAgent(openaiApiKey);
  const patientAgent = new PatientAgent(openaiApiKey);
  const journeyAgent = new JourneyAgent(openaiApiKey);
  const communicationAgent = new CommunicationAgent(openaiApiKey);
  const ticketAgent = new TicketAgent(openaiApiKey);

  agentRegistry.registerAgent(
    appointmentAgent,
    appointmentAgent.getCapabilities(),
    10 // High priority for appointment agent
  );

  agentRegistry.registerAgent(
    patientAgent,
    patientAgent.getCapabilities(),
    10 // High priority for patient agent
  );

  agentRegistry.registerAgent(
    journeyAgent,
    journeyAgent.getCapabilities(),
    9 // Slightly lower priority
  );

  agentRegistry.registerAgent(
    communicationAgent,
    communicationAgent.getCapabilities(),
    9 // Slightly lower priority
  );

  agentRegistry.registerAgent(
    ticketAgent,
    ticketAgent.getCapabilities(),
    8 // Lower priority
  );

  console.log('AI System initialized successfully');
  console.log(`- ${toolRegistry.getToolCount()} tools registered`);
  console.log(`- ${agentRegistry.getAgentCount()} agents registered`);
}

/**
 * Get AI system status
 */
export function getAISystemStatus() {
  return {
    tools: {
      count: toolRegistry.getToolCount(),
      categories: toolRegistry.getAllCategories(),
    },
    agents: {
      count: agentRegistry.getAgentCount(),
      metadata: agentRegistry.getAllMetadata(),
    },
    sessions: {
      active: orchestrator.getActiveSessions().length,
    },
  };
}

/**
 * Process user input through the AI system
 */
export async function processUserInput(
  input: string,
  userId: string,
  orgId: string,
  sessionId: string,
  permissions: string[] = []
) {
  return orchestrator.process(input, {
    userId,
    orgId,
    sessionId,
    requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    permissions,
  });
}

/**
 * Execute a confirmed plan (called after user clicks "Confirm Action")
 */
export async function executeConfirmedPlan(
  plan: any,
  agentName: string,
  userId: string,
  orgId: string,
  sessionId: string,
  permissions: string[] = []
) {
  const agent = agentRegistry.getAgent(agentName);

  if (!agent) {
    return {
      success: false,
      message: `Agent ${agentName} not found`,
      error: { code: 'AGENT_NOT_FOUND', message: `Agent ${agentName} not found` },
    };
  }

  const context = {
    userId,
    orgId,
    sessionId,
    requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    permissions,
  };

  console.log('🚀 [AI Debug] Executing confirmed plan...');
  console.log('📋 Agent:', agentName);
  console.log('📝 Plan:', JSON.stringify(plan, null, 2));

  // Call the agent's executeWithConfirmation method
  const result = await agent.executeWithConfirmation(plan, context);

  console.log('✅ [AI Debug] Execution result:', result);

  return result;
}

// Export singleton instances
export { orchestrator, toolRegistry, agentRegistry, intentParser };

// Export classes for custom implementations
export { AppointmentAgent } from './agents/AppointmentAgent';
export { PatientAgent } from './agents/PatientAgent';
export { JourneyAgent } from './agents/JourneyAgent';
export { CommunicationAgent } from './agents/CommunicationAgent';
export { BaseAgent } from './agents/BaseAgent';
export { ToolRegistry } from './tools/registry';
export { AgentRegistry } from './agents/registry';
export { IntentParser } from './intent-parser';
export { Orchestrator } from './orchestrator';
