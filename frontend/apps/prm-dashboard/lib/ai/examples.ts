/**
 * AI System Usage Examples
 * Demonstrates how to use the AI system in various scenarios
 */

import {
  initializeAISystem,
  processUserInput,
  getAISystemStatus,
  orchestrator,
} from './index';

/**
 * Example 1: Basic Setup
 */
export async function example1_basicSetup() {
  console.log('=== Example 1: Basic Setup ===\n');

  // Initialize the AI system
  initializeAISystem(process.env.OPENAI_API_KEY);

  // Check system status
  const status = getAISystemStatus();
  console.log('System Status:', JSON.stringify(status, null, 2));

  console.log('\n✅ AI System initialized successfully\n');
}

/**
 * Example 2: Simple Appointment Query
 */
export async function example2_simpleAppointmentQuery() {
  console.log('=== Example 2: Simple Appointment Query ===\n');

  const result = await processUserInput(
    'Show me available slots for cardiology tomorrow',
    'user_123',
    'org_456',
    'session_1'
  );

  console.log('User Input:', 'Show me available slots for cardiology tomorrow');
  console.log('\nResult:');
  console.log('- Success:', result.success);
  console.log('- Message:', result.message);
  console.log('- Agents Used:', result.agentsUsed);
  console.log(
    '- Execution Time:',
    result.metadata?.executionTime + 'ms'
  );

  console.log('\n✅ Appointment query completed\n');
}

/**
 * Example 3: Patient Search
 */
export async function example3_patientSearch() {
  console.log('=== Example 3: Patient Search ===\n');

  const result = await processUserInput(
    'Search for patient with phone 9844111173',
    'user_123',
    'org_456',
    'session_2'
  );

  console.log('User Input:', 'Search for patient with phone 9844111173');
  console.log('\nResult:');
  console.log('- Success:', result.success);
  console.log('- Message:', result.message);
  console.log('- Agents Used:', result.agentsUsed);
  console.log('- Data:', JSON.stringify(result.results[0]?.data, null, 2));

  console.log('\n✅ Patient search completed\n');
}

/**
 * Example 4: Complex Multi-Agent Request
 */
export async function example4_complexMultiAgent() {
  console.log('=== Example 4: Complex Multi-Agent Request ===\n');

  const result = await processUserInput(
    'Book John Doe for a cardiology consultation next Monday at 2pm',
    'user_123',
    'org_456',
    'session_3',
    ['appointments.write', 'patients.read']
  );

  console.log(
    'User Input:',
    'Book John Doe for a cardiology consultation next Monday at 2pm'
  );
  console.log('\nResult:');
  console.log('- Success:', result.success);
  console.log('- Message:', result.message);
  console.log('- Agents Used:', result.agentsUsed);
  console.log('- Total Steps:', result.metadata?.totalSteps);
  console.log(
    '- Execution Time:',
    result.metadata?.executionTime + 'ms'
  );

  console.log('\n✅ Multi-agent request completed\n');
}

/**
 * Example 5: Confirmation Required
 */
export async function example5_confirmationRequired() {
  console.log('=== Example 5: Confirmation Required ===\n');

  const result = await processUserInput(
    'Cancel appointment APT123',
    'user_123',
    'org_456',
    'session_4',
    ['appointments.write']
  );

  console.log('User Input:', 'Cancel appointment APT123');
  console.log('\nResult:');
  console.log('- Success:', result.success);
  console.log('- Message:', result.message);

  if (result.results[0]?.data?.requiresConfirmation) {
    console.log('\n⚠️  Confirmation Required!');
    console.log('Plan:', JSON.stringify(result.results[0].data.plan, null, 2));
    console.log('\n→ User should review and confirm this action');
  }

  console.log('\n✅ Confirmation workflow demonstrated\n');
}

/**
 * Example 6: Low Confidence / Clarification Needed
 */
export async function example6_clarificationNeeded() {
  console.log('=== Example 6: Clarification Needed ===\n');

  const result = await processUserInput(
    'Schedule something',
    'user_123',
    'org_456',
    'session_5'
  );

  console.log('User Input:', 'Schedule something (intentionally vague)');
  console.log('\nResult:');
  console.log('- Success:', result.success);
  console.log('- Message:', result.message);

  if (result.metadata?.requiresClarification) {
    console.log('\n❓ Clarification Questions:');
    result.metadata.clarifications?.forEach((q: string, i: number) => {
      console.log(`${i + 1}. ${q}`);
    });
  }

  console.log('\n✅ Clarification workflow demonstrated\n');
}

/**
 * Example 7: Conversation History
 */
export async function example7_conversationHistory() {
  console.log('=== Example 7: Conversation History ===\n');

  const sessionId = 'session_history_demo';

  // Message 1
  await processUserInput(
    'Show available slots for tomorrow',
    'user_123',
    'org_456',
    sessionId
  );
  console.log('1. User: Show available slots for tomorrow');

  // Message 2
  await processUserInput(
    'Book the 2pm slot for John Doe',
    'user_123',
    'org_456',
    sessionId
  );
  console.log('2. User: Book the 2pm slot for John Doe');

  // Message 3
  await processUserInput(
    'Send confirmation to the patient',
    'user_123',
    'org_456',
    sessionId
  );
  console.log('3. User: Send confirmation to the patient');

  // Get conversation summary
  const summary = orchestrator.getConversationSummary(sessionId);
  console.log('\nConversation Summary:');
  console.log('- Total Messages:', summary.messageCount);
  console.log('- User Messages:', summary.userMessages);
  console.log('- Assistant Messages:', summary.assistantMessages);
  console.log(
    '- Last Message:',
    summary.lastMessage?.role + ': ' + summary.lastMessage?.content?.substring(0, 50) + '...'
  );

  console.log('\n✅ Conversation history tracked\n');
}

/**
 * Example 8: Error Handling
 */
export async function example8_errorHandling() {
  console.log('=== Example 8: Error Handling ===\n');

  const result = await processUserInput(
    'Cancel appointment INVALID_ID',
    'user_123',
    'org_456',
    'session_error'
  );

  console.log('User Input:', 'Cancel appointment INVALID_ID');
  console.log('\nResult:');
  console.log('- Success:', result.success);
  console.log('- Message:', result.message);

  if (!result.success && result.error) {
    console.log('\n❌ Error Details:');
    console.log('- Code:', result.error.code);
    console.log('- Message:', result.error.message);
  }

  console.log('\n✅ Error handling demonstrated\n');
}

/**
 * Example 9: Agent Capabilities
 */
export async function example9_agentCapabilities() {
  console.log('=== Example 9: Agent Capabilities ===\n');

  const status = getAISystemStatus();

  console.log('Available Agents and Their Capabilities:\n');

  status.agents.metadata.forEach((meta) => {
    console.log(`\n📋 ${meta.name}`);
    console.log(`   ${meta.description}\n`);

    meta.capabilities.forEach((cap) => {
      console.log(`   ✓ ${cap.name}`);
      console.log(`     ${cap.description}`);
      console.log(`     Examples:`);
      cap.examples.forEach((ex: string) => {
        console.log(`       - "${ex}"`);
      });
      console.log('');
    });
  });

  console.log('✅ All agent capabilities listed\n');
}

/**
 * Example 10: Performance Monitoring
 */
export async function example10_performanceMonitoring() {
  console.log('=== Example 10: Performance Monitoring ===\n');

  const queries = [
    'Show available slots for tomorrow',
    'Search for patient John Doe',
    'Book appointment for patient 123',
  ];

  console.log('Running performance tests...\n');

  const results = await Promise.all(
    queries.map(async (query, index) => {
      const start = Date.now();
      const result = await processUserInput(
        query,
        'user_123',
        'org_456',
        `perf_session_${index}`
      );
      const end = Date.now();

      return {
        query,
        executionTime: end - start,
        success: result.success,
        agentsUsed: result.agentsUsed,
        stepsCompleted: result.metadata?.totalSteps || 0,
      };
    })
  );

  console.log('Performance Results:\n');
  results.forEach((r, i) => {
    console.log(`${i + 1}. "${r.query}"`);
    console.log(`   ⏱️  ${r.executionTime}ms`);
    console.log(`   ✅ Success: ${r.success}`);
    console.log(`   🤖 Agents: ${r.agentsUsed.join(', ')}`);
    console.log(`   📊 Steps: ${r.stepsCompleted}`);
    console.log('');
  });

  const avgTime =
    results.reduce((sum, r) => sum + r.executionTime, 0) / results.length;
  console.log(`Average Execution Time: ${Math.round(avgTime)}ms\n`);

  console.log('✅ Performance monitoring completed\n');
}

/**
 * Run all examples
 */
export async function runAllExamples() {
  console.log('\n');
  console.log('='.repeat(60));
  console.log('AI SYSTEM EXAMPLES');
  console.log('='.repeat(60));
  console.log('\n');

  await example1_basicSetup();
  await example2_simpleAppointmentQuery();
  await example3_patientSearch();
  await example4_complexMultiAgent();
  await example5_confirmationRequired();
  await example6_clarificationNeeded();
  await example7_conversationHistory();
  await example8_errorHandling();
  await example9_agentCapabilities();
  await example10_performanceMonitoring();

  console.log('='.repeat(60));
  console.log('ALL EXAMPLES COMPLETED');
  console.log('='.repeat(60));
  console.log('\n');
}

// Export individual examples
export {
  example1_basicSetup as basicSetup,
  example2_simpleAppointmentQuery as simpleQuery,
  example3_patientSearch as patientSearch,
  example4_complexMultiAgent as complexRequest,
  example5_confirmationRequired as confirmationFlow,
  example6_clarificationNeeded as clarificationFlow,
  example7_conversationHistory as conversationTracking,
  example8_errorHandling as errorHandling,
  example9_agentCapabilities as agentCapabilities,
  example10_performanceMonitoring as performanceMonitoring,
};
