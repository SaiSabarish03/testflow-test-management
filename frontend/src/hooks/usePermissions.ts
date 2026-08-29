import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types';

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role ?? null;

  const hasRole = (...roles: UserRole[]): boolean =>
    role !== null && (roles as string[]).includes(role);

  return {
    role,
    isAdmin: role === 'ADMIN',
    isQaEngineer: role === 'QA_ENGINEER',
    isViewer: role === 'VIEWER',
    canWrite: hasRole('ADMIN', 'QA_ENGINEER'),
    canManageUsers: hasRole('ADMIN'),
    hasRole,
  };
}
