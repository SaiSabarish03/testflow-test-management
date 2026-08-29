import { Tag } from 'antd';
import type { ProjectStatus, TestRunStatus, TestResultStatus, DefectStatus, DefectSeverity } from '../../types';

type StatusValue = ProjectStatus | TestRunStatus | TestResultStatus | DefectStatus | DefectSeverity | string;

const COLOR_MAP: Record<string, string> = {
  // Project
  ACTIVE: 'green',
  ARCHIVED: 'default',
  // Test run
  NOT_STARTED: 'default',
  IN_PROGRESS: 'blue',
  COMPLETED: 'green',
  ABORTED: 'red',
  // Test result
  NOT_RUN: 'default',
  PASSED: 'green',
  FAILED: 'red',
  BLOCKED: 'orange',
  // Defect status
  OPEN: 'red',
  RESOLVED: 'cyan',
  CLOSED: 'default',
  REJECTED: 'volcano',
  // Defect severity
  BLOCKER: 'red',
  CRITICAL: 'volcano',
  MAJOR: 'orange',
  MINOR: 'gold',
  TRIVIAL: 'default',
  // Test case
  DRAFT: 'default',
  READY: 'green',
  DEPRECATED: 'volcano',
};

interface Props {
  value: StatusValue;
  label?: string;
}

export function StatusTag({ value, label }: Props) {
  const color = COLOR_MAP[value] ?? 'default';
  return <Tag color={color}>{label ?? value}</Tag>;
}
