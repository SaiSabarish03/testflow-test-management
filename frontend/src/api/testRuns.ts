import { apiClient } from './client';
import type { TestRun, TestResult, TestRunSummary, PaginatedResponse } from '../types';

export async function listRuns(
  projectId: number,
  params: { search?: string; status?: string; environment?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedResponse<TestRun>> {
  const { data } = await apiClient.get<PaginatedResponse<TestRun>>(
    `/api/projects/${projectId}/runs`,
    { params },
  );
  return data;
}

export async function getRun(runId: number): Promise<TestRun> {
  const { data } = await apiClient.get<TestRun>(`/api/runs/${runId}`);
  return data;
}

export async function createRun(
  projectId: number,
  payload: { name: string; environment: string; test_case_ids: number[] },
): Promise<TestRun> {
  const { data } = await apiClient.post<TestRun>(
    `/api/projects/${projectId}/runs`,
    payload,
  );
  return data;
}

export async function startRun(runId: number): Promise<TestRun> {
  const { data } = await apiClient.post<TestRun>(`/api/runs/${runId}/start`);
  return data;
}

export async function completeRun(runId: number): Promise<TestRun> {
  const { data } = await apiClient.post<TestRun>(`/api/runs/${runId}/complete`);
  return data;
}

export async function abortRun(runId: number): Promise<TestRun> {
  const { data } = await apiClient.post<TestRun>(`/api/runs/${runId}/abort`);
  return data;
}

export async function getRunSummary(runId: number): Promise<TestRunSummary> {
  const { data } = await apiClient.get<TestRunSummary>(`/api/runs/${runId}/summary`);
  return data;
}

export async function listResults(
  runId: number,
  params: { status?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedResponse<TestResult>> {
  const { data } = await apiClient.get<PaginatedResponse<TestResult>>(
    `/api/runs/${runId}/results`,
    { params },
  );
  return data;
}

export async function recordResult(
  runId: number,
  resultId: number,
  payload: { status: string; actual_result?: string },
): Promise<TestResult> {
  const { data } = await apiClient.put<TestResult>(
    `/api/runs/${runId}/results/${resultId}`,
    payload,
  );
  return data;
}
