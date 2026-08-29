import type { ProjectStatus, TestCaseStatus, TestRunStatus, TestResultStatus, DefectStatus, DefectSeverity, DefectPriority } from '../types';

export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  ACTIVE: 'Active',
  ARCHIVED: 'Archived',
};

export const TEST_CASE_STATUS_LABELS: Record<TestCaseStatus, string> = {
  DRAFT: 'Draft',
  READY: 'Ready',
  DEPRECATED: 'Deprecated',
};

export const TEST_RUN_STATUS_LABELS: Record<TestRunStatus, string> = {
  NOT_STARTED: 'Not Started',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Completed',
  ABORTED: 'Aborted',
};

export const TEST_RESULT_STATUS_LABELS: Record<TestResultStatus, string> = {
  NOT_RUN: 'Not Run',
  PASSED: 'Passed',
  FAILED: 'Failed',
  BLOCKED: 'Blocked',
};

export const DEFECT_STATUS_LABELS: Record<DefectStatus, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
  CLOSED: 'Closed',
  REJECTED: 'Rejected',
};

export const DEFECT_SEVERITY_LABELS: Record<DefectSeverity, string> = {
  BLOCKER: 'Blocker',
  CRITICAL: 'Critical',
  MAJOR: 'Major',
  MINOR: 'Minor',
  TRIVIAL: 'Trivial',
};

export const DEFECT_PRIORITY_LABELS: Record<DefectPriority, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Critical',
};

export const PAGE_SIZE_DEFAULT = 20;
