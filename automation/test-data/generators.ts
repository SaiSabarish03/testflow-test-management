/** Generate a unique suffix to avoid test collisions. */
function uid(): string {
  return Date.now().toString(36).toUpperCase();
}

export function uniqueProjectKey(): string {
  return `TP${uid()}`.slice(0, 10);
}

export function uniqueProjectName(): string {
  return `Test Project ${uid()}`;
}

export function uniqueSuiteName(): string {
  return `Suite ${uid()}`;
}

export function uniqueTestCaseTitle(): string {
  return `TC ${uid()}`;
}

export function uniqueRunName(): string {
  return `Run ${uid()}`;
}

export function uniqueDefectTitle(): string {
  return `Defect ${uid()}`;
}

export function uniqueUserEmail(): string {
  return `user.${uid().toLowerCase()}@example.com`;
}

export function uniqueUserName(): string {
  return `User ${uid()}`;
}
