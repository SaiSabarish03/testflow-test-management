import { apiClient } from './client';
import type { TestCase, PaginatedResponse } from '../types';

export interface TestStep {
  order: number;
  action: string;
}

export interface CreateTestCasePayload {
  title: string;
  description?: string;
  preconditions?: string;
  steps?: TestStep[];
  expected_result: string;
  priority: string;
  status?: string;
}

export interface UpdateTestCasePayload {
  title?: string;
  description?: string;
  preconditions?: string;
  steps?: TestStep[];
  expected_result?: string;
  priority?: string;
  status?: string;
}

export async function listTestCases(
  suiteId: number,
  params: { search?: string; priority?: string; status?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedResponse<TestCase>> {
  const { data } = await apiClient.get<PaginatedResponse<TestCase>>(
    `/api/suites/${suiteId}/test-cases`,
    { params },
  );
  return data;
}

export async function getTestCase(testCaseId: number): Promise<TestCase> {
  const { data } = await apiClient.get<TestCase>(`/api/test-cases/${testCaseId}`);
  return data;
}

export async function createTestCase(
  suiteId: number,
  payload: CreateTestCasePayload,
): Promise<TestCase> {
  const { data } = await apiClient.post<TestCase>(
    `/api/suites/${suiteId}/test-cases`,
    payload,
  );
  return data;
}

export async function updateTestCase(
  testCaseId: number,
  payload: UpdateTestCasePayload,
): Promise<TestCase> {
  const { data } = await apiClient.put<TestCase>(
    `/api/test-cases/${testCaseId}`,
    payload,
  );
  return data;
}

/** Deprecates the test case (backend soft-delete via DELETE). */
export async function deprecateTestCase(testCaseId: number): Promise<TestCase> {
  const { data } = await apiClient.delete<TestCase>(`/api/test-cases/${testCaseId}`);
  return data;
}
