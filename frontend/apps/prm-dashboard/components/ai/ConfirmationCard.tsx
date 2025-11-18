'use client';

import { useState } from 'react';
import {
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { AgentPlan } from '@/lib/ai/agents/BaseAgent';
import { agentRegistry } from '@/lib/ai';
import { ExecutionContext } from '@/lib/ai/tools/types';
import toast from 'react-hot-toast';

/**
 * Confirmation Card Props
 */
interface ConfirmationCardProps {
  plan: AgentPlan;
  agentName: string;
  context: ExecutionContext;
  onConfirm?: (result: any) => void;
  onCancel?: () => void;
}

/**
 * ConfirmationCard Component
 * Beautiful card for confirming AI actions before execution
 */
export function ConfirmationCard({
  plan,
  agentName,
  context,
  onConfirm,
  onCancel,
}: ConfirmationCardProps) {
  const [isExecuting, setIsExecuting] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  /**
   * Handle confirmation
   */
  const handleConfirm = async () => {
    setIsExecuting(true);

    try {
      const agent = agentRegistry.getAgent(agentName);

      if (!agent) {
        toast.error('Agent not found');
        return;
      }

      const result = await agent.executeWithConfirmation(plan, context);

      if (result.success) {
        toast.success('Action completed successfully');
      } else {
        toast.error('Action failed: ' + result.error?.message);
      }

      if (onConfirm) {
        onConfirm(result);
      }
    } catch (error: any) {
      console.error('Confirmation execution error:', error);
      toast.error('Failed to execute action');
    } finally {
      setIsExecuting(false);
    }
  };

  /**
   * Get risk level color
   */
  const getRiskLevelColor = (level?: string) => {
    switch (level) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  /**
   * Get risk level icon
   */
  const getRiskLevelIcon = (level?: string) => {
    switch (level) {
      case 'high':
        return <AlertCircle className="w-5 h-5" />;
      case 'medium':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <CheckCircle className="w-5 h-5" />;
    }
  };

  // Determine overall risk level (highest among all steps)
  const overallRiskLevel =
    plan.steps.some((s) => s.toolName.includes('delete')) ||
    plan.steps.some((s) => s.toolName.includes('cancel'))
      ? 'medium'
      : 'low';

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden max-w-2xl mx-auto">
      {/* Header */}
      <div
        className={`px-6 py-4 border-b flex items-center gap-3 ${getRiskLevelColor(overallRiskLevel)}`}
      >
        {getRiskLevelIcon(overallRiskLevel)}
        <div className="flex-1">
          <h3 className="font-semibold">Confirmation Required</h3>
          <p className="text-sm opacity-80">
            Please review the action before proceeding
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-5">
        {/* Reasoning */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            What I'm about to do:
          </h4>
          <p className="text-gray-900">{plan.reasoning}</p>
        </div>

        {/* Steps Summary */}
        <div className="mb-4">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
          >
            {showDetails ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
            {plan.steps.length} step{plan.steps.length > 1 ? 's' : ''} planned
          </button>

          {showDetails && (
            <div className="mt-3 space-y-2">
              {plan.steps.map((step, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-3 border border-gray-200"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm text-gray-900">
                        {step.toolName}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {step.reasoning}
                      </div>
                      <div className="mt-2">
                        <details className="text-xs text-gray-500">
                          <summary className="cursor-pointer hover:text-gray-700">
                            Parameters
                          </summary>
                          <pre className="mt-2 bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(step.params, null, 2)}
                          </pre>
                        </details>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Agent Info */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="font-medium">Agent:</span>
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
            {agentName}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t flex items-center justify-end gap-3">
        <button
          onClick={onCancel}
          disabled={isExecuting}
          className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <XCircle className="w-4 h-4" />
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={isExecuting}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isExecuting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Executing...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              Confirm & Execute
            </>
          )}
        </button>
      </div>
    </div>
  );
}

/**
 * Confirmation Modal Wrapper
 */
export function ConfirmationModal({
  isOpen,
  plan,
  agentName,
  context,
  onConfirm,
  onCancel,
}: {
  isOpen: boolean;
  plan: AgentPlan;
  agentName: string;
  context: ExecutionContext;
  onConfirm?: (result: any) => void;
  onCancel?: () => void;
}) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in duration-200"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl px-4 animate-in zoom-in-95 duration-200">
        <ConfirmationCard
          plan={plan}
          agentName={agentName}
          context={context}
          onConfirm={onConfirm}
          onCancel={onCancel}
        />
      </div>
    </>
  );
}
