// ─── Enums ────────────────────────────────────────────────────────────────────

export type UserRole = 'ADMIN' | 'QA_ENGINEER' | 'VIEWER';
export type UserStatus = 'ACTIVE' | 'INACTIVE';

export type ProjectStatus = 'ACTIVE' | 'ARCHIVED';

export type TestCasePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type TestCaseStatus = 'DRAFT' | 'READY' | 'DEPRECATED';

export type TestRunStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'ABORTED';
export type TestResultStatus = 'NOT_RUN' | 'PASSED' | 'FAILED' | 'BLOCKED';

export type DefectSeverity = 'BLOCKER' | 'CRITICAL' | 'MAJOR' | 'MINOR' | 'TRIVIAL';
export type DefectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type DefectStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'REJECTED';

// ─── Domain models ────────────────────────────────────────────────────────────

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: number;
  name: string;
  key: string;
  description: string | null;
  status: ProjectStatus;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface TestSuite {
  id: number;
  project_id: number;
  name: string;
  description: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: number;
  suite_id: number;
  title: string;
  description: string | null;
  preconditions: string | null;
  steps: Array<{ order: number; action: string }> | null;
  expected_result: string;
  priority: TestCasePriority;
  status: TestCaseStatus;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface TestRun {
  id: number;
  project_id: number;
  name: string;
  environment: string;
  status: TestRunStatus;
  started_at: string | null;
  completed_at: string | null;
  created_by: number;
  created_at: string;
}

export interface TestCaseMinimal {
  id: number;
  title: string;
  suite_id: number;
}

export interface TestResult {
  id: number;
  test_run_id: number;
  test_case_id: number;
  status: TestResultStatus;
  actual_result: string | null;
  executed_by: number | null;
  executed_at: string | null;
  test_case: TestCaseMinimal | null;
}

export interface TestRunSummary {
  total: number;
  not_run: number;
  passed: number;
  failed: number;
  blocked: number;
  pass_rate: number;
}

export interface Defect {
  id: number;
  project_id: number;
  test_case_id: number | null;
  title: string;
  description: string | null;
  severity: DefectSeverity;
  priority: DefectPriority;
  environment: string | null;
  status: DefectStatus;
  created_by: number;
  assigned_to: number | null;
  created_at: string;
  updated_at: string;
}

// ─── Pagination wrapper ───────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}
