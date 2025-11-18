'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated, hasPermission, hasRole, getCurrentUser, User } from './auth';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

/**
 * Auth Guard - Requires authentication
 */
export function AuthGuard({ children, fallback, redirectTo = '/login' }: AuthGuardProps) {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push(redirectTo);
    }
  }, [router, redirectTo]);

  if (!isAuthenticated()) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return <>{children}</>;
}

interface PermissionGuardProps extends AuthGuardProps {
  permissions: string | string[];
  requireAll?: boolean;
}

/**
 * Permission Guard - Requires specific permissions
 */
export function PermissionGuard({
  children,
  permissions,
  requireAll = false,
  fallback,
  redirectTo = '/unauthorized',
}: PermissionGuardProps) {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const perms = Array.isArray(permissions) ? permissions : [permissions];
    const hasAccess = requireAll
      ? perms.every((p) => hasPermission(p))
      : perms.some((p) => hasPermission(p));

    if (!hasAccess) {
      router.push(redirectTo);
    }
  }, [permissions, requireAll, router, redirectTo]);

  if (!isAuthenticated()) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const perms = Array.isArray(permissions) ? permissions : [permissions];
  const hasAccess = requireAll
    ? perms.every((p) => hasPermission(p))
    : perms.some((p) => hasPermission(p));

  if (!hasAccess) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access this resource.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

interface RoleGuardProps extends AuthGuardProps {
  roles: User['role'] | User['role'][];
}

/**
 * Role Guard - Requires specific role(s)
 */
export function RoleGuard({
  children,
  roles,
  fallback,
  redirectTo = '/unauthorized',
}: RoleGuardProps) {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    if (!hasRole(roles)) {
      router.push(redirectTo);
    }
  }, [roles, router, redirectTo]);

  if (!isAuthenticated()) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!hasRole(roles)) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">Your role doesn't have access to this resource.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Guest Guard - Only for unauthenticated users (login, register pages)
 */
export function GuestGuard({ children, redirectTo = '/' }: Omit<AuthGuardProps, 'fallback'>) {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.push(redirectTo);
    }
  }, [router, redirectTo]);

  if (isAuthenticated()) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Hook to use auth guards programmatically
 */
export function useAuthGuard() {
  const router = useRouter();

  const requireAuth = (redirectTo = '/login') => {
    if (!isAuthenticated()) {
      router.push(redirectTo);
      return false;
    }
    return true;
  };

  const requirePermission = (permission: string | string[], requireAll = false) => {
    if (!isAuthenticated()) {
      router.push('/login');
      return false;
    }

    const perms = Array.isArray(permission) ? permission : [permission];
    const hasAccess = requireAll
      ? perms.every((p) => hasPermission(p))
      : perms.some((p) => hasPermission(p));

    if (!hasAccess) {
      router.push('/unauthorized');
      return false;
    }

    return true;
  };

  const requireRole = (role: User['role'] | User['role'][]) => {
    if (!isAuthenticated()) {
      router.push('/login');
      return false;
    }

    if (!hasRole(role)) {
      router.push('/unauthorized');
      return false;
    }

    return true;
  };

  return {
    requireAuth,
    requirePermission,
    requireRole,
    isAuthenticated: isAuthenticated(),
    user: getCurrentUser(),
  };
}

/**
 * Conditional render based on permissions
 */
export function CanAccess({
  permission,
  children,
  fallback = null,
}: {
  permission: string | string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const perms = Array.isArray(permission) ? permission : [permission];
  const hasAccess = perms.some((p) => hasPermission(p));

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Conditional render based on role
 */
export function CanAccessRole({
  role,
  children,
  fallback = null,
}: {
  role: User['role'] | User['role'][];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const hasAccess = hasRole(role);

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
