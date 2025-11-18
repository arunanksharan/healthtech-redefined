/**
 * Audit Logging System
 * HIPAA compliant audit logging for all PHI access and modifications
 */

import { getCurrentUser } from '../auth/auth';

export type AuditAction =
  // Patient actions
  | 'patient.view'
  | 'patient.create'
  | 'patient.update'
  | 'patient.delete'
  | 'patient.search'
  // Appointment actions
  | 'appointment.view'
  | 'appointment.create'
  | 'appointment.update'
  | 'appointment.cancel'
  | 'appointment.reschedule'
  // Journey actions
  | 'journey.view'
  | 'journey.create'
  | 'journey.update'
  | 'journey.complete'
  // Communication actions
  | 'communication.send'
  | 'communication.view'
  // Ticket actions
  | 'ticket.view'
  | 'ticket.create'
  | 'ticket.update'
  | 'ticket.assign'
  | 'ticket.resolve'
  // Auth actions
  | 'auth.login'
  | 'auth.logout'
  | 'auth.failed_login'
  | 'auth.password_change'
  // Data export
  | 'data.export'
  | 'data.download'
  // Settings
  | 'settings.update'
  | 'settings.view';

export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface AuditLogEntry {
  id?: string;
  timestamp: string;
  action: AuditAction;
  severity: AuditSeverity;
  user_id: string;
  user_email: string;
  user_role: string;
  org_id: string;
  resource_type?: string;
  resource_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  success: boolean;
  error_message?: string;
  session_id?: string;
}

/**
 * Log audit event
 */
export async function logAudit(
  action: AuditAction,
  options: {
    severity?: AuditSeverity;
    resourceType?: string;
    resourceId?: string;
    details?: Record<string, any>;
    success?: boolean;
    errorMessage?: string;
  } = {}
): Promise<void> {
  const user = getCurrentUser();
  if (!user) {
    console.warn('Audit log attempted without authenticated user');
    return;
  }

  const entry: AuditLogEntry = {
    timestamp: new Date().toISOString(),
    action,
    severity: options.severity || getSeverityForAction(action),
    user_id: user.id,
    user_email: user.email,
    user_role: user.role,
    org_id: user.org_id,
    resource_type: options.resourceType,
    resource_id: options.resourceId,
    details: sanitizeDetails(options.details),
    ip_address: await getClientIP(),
    user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
    success: options.success !== false,
    error_message: options.errorMessage,
    session_id: getSessionId(),
  };

  // Send to backend audit log service
  try {
    await sendAuditLog(entry);
  } catch (error) {
    // Fallback: log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('AUDIT LOG:', entry);
    }
    // In production, this should queue for retry
    console.error('Failed to send audit log:', error);
  }
}

/**
 * Send audit log to backend
 */
async function sendAuditLog(entry: AuditLogEntry): Promise<void> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/audit-logs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('auth_access_token')}`,
    },
    body: JSON.stringify(entry),
  });

  if (!response.ok) {
    throw new Error('Failed to send audit log');
  }
}

/**
 * Get severity level for action
 */
function getSeverityForAction(action: AuditAction): AuditSeverity {
  // Critical: Data export, deletion, auth failures
  if (
    action.includes('delete') ||
    action.includes('export') ||
    action.includes('failed_login') ||
    action === 'auth.password_change'
  ) {
    return 'critical';
  }

  // High: Create, update, send communications
  if (
    action.includes('create') ||
    action.includes('update') ||
    action.includes('send') ||
    action.includes('assign')
  ) {
    return 'high';
  }

  // Medium: View patient data, cancel appointments
  if (
    action === 'patient.view' ||
    action === 'appointment.cancel' ||
    action === 'journey.complete'
  ) {
    return 'medium';
  }

  // Low: Everything else
  return 'low';
}

/**
 * Sanitize details to remove sensitive data
 */
function sanitizeDetails(details?: Record<string, any>): Record<string, any> | undefined {
  if (!details) return undefined;

  const sanitized = { ...details };

  // Remove sensitive fields
  const sensitiveFields = [
    'password',
    'ssn',
    'social_security_number',
    'credit_card',
    'card_number',
    'cvv',
    'api_key',
    'secret',
    'token',
  ];

  for (const field of sensitiveFields) {
    if (field in sanitized) {
      sanitized[field] = '[REDACTED]';
    }
  }

  return sanitized;
}

/**
 * Get client IP address
 */
async function getClientIP(): Promise<string | undefined> {
  // In production, this should be set by the server
  // For now, we'll use a placeholder
  return undefined;
}

/**
 * Get session ID
 */
function getSessionId(): string {
  if (typeof window === 'undefined') return '';

  let sessionId = sessionStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('session_id', sessionId);
  }
  return sessionId;
}

/**
 * Audit log helper for patient actions
 */
export const auditPatient = {
  view: (patientId: string) =>
    logAudit('patient.view', {
      resourceType: 'patient',
      resourceId: patientId,
      severity: 'medium',
    }),

  create: (patientId: string, details?: Record<string, any>) =>
    logAudit('patient.create', {
      resourceType: 'patient',
      resourceId: patientId,
      details,
      severity: 'high',
    }),

  update: (patientId: string, changes: Record<string, any>) =>
    logAudit('patient.update', {
      resourceType: 'patient',
      resourceId: patientId,
      details: { changes },
      severity: 'high',
    }),

  delete: (patientId: string) =>
    logAudit('patient.delete', {
      resourceType: 'patient',
      resourceId: patientId,
      severity: 'critical',
    }),

  search: (query: string, resultCount: number) =>
    logAudit('patient.search', {
      details: { query, result_count: resultCount },
      severity: 'medium',
    }),
};

/**
 * Audit log helper for appointment actions
 */
export const auditAppointment = {
  view: (appointmentId: string) =>
    logAudit('appointment.view', {
      resourceType: 'appointment',
      resourceId: appointmentId,
    }),

  create: (appointmentId: string, patientId: string) =>
    logAudit('appointment.create', {
      resourceType: 'appointment',
      resourceId: appointmentId,
      details: { patient_id: patientId },
      severity: 'high',
    }),

  update: (appointmentId: string, changes: Record<string, any>) =>
    logAudit('appointment.update', {
      resourceType: 'appointment',
      resourceId: appointmentId,
      details: { changes },
      severity: 'high',
    }),

  cancel: (appointmentId: string, reason: string) =>
    logAudit('appointment.cancel', {
      resourceType: 'appointment',
      resourceId: appointmentId,
      details: { reason },
      severity: 'medium',
    }),

  reschedule: (appointmentId: string, oldDate: string, newDate: string) =>
    logAudit('appointment.reschedule', {
      resourceType: 'appointment',
      resourceId: appointmentId,
      details: { old_date: oldDate, new_date: newDate },
      severity: 'high',
    }),
};

/**
 * Audit log helper for communication actions
 */
export const auditCommunication = {
  send: (channel: string, recipientCount: number, patientIds?: string[]) =>
    logAudit('communication.send', {
      resourceType: 'communication',
      details: {
        channel,
        recipient_count: recipientCount,
        patient_ids: patientIds,
      },
      severity: 'high',
    }),

  view: (communicationId: string) =>
    logAudit('communication.view', {
      resourceType: 'communication',
      resourceId: communicationId,
    }),
};

/**
 * Audit log helper for auth actions
 */
export const auditAuth = {
  login: (userId: string, email: string) =>
    logAudit('auth.login', {
      details: { user_id: userId, email },
      severity: 'medium',
    }),

  logout: () =>
    logAudit('auth.logout', {
      severity: 'low',
    }),

  failedLogin: (email: string, reason: string) =>
    logAudit('auth.failed_login', {
      details: { email, reason },
      success: false,
      errorMessage: reason,
      severity: 'critical',
    }),

  passwordChange: (userId: string) =>
    logAudit('auth.password_change', {
      details: { user_id: userId },
      severity: 'critical',
    }),
};

/**
 * Audit log helper for data export
 */
export const auditDataExport = {
  export: (dataType: string, recordCount: number, format: string) =>
    logAudit('data.export', {
      details: {
        data_type: dataType,
        record_count: recordCount,
        format,
      },
      severity: 'critical',
    }),

  download: (resourceType: string, resourceId: string) =>
    logAudit('data.download', {
      resourceType,
      resourceId,
      severity: 'critical',
    }),
};
