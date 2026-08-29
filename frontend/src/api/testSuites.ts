import { apiClient } from './client';
import type { TestSuite, PaginatedResponse } from '../types';

export async function listSuites(
  projectId: number,
  params: { search?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedResponse<TestSuite>> {
  const { data } = await apiClient.get<PaginatedResponse<TestSuite>>(
    `/api/projects/${projectId}/suites`,
    { params },
  );
  return data;
}

export async function getSuite(suiteId: number): Promise<TestSuite> {
  const { data } = await apiClient.get<TestSuite>(`/api/suites/${suiteId}`);
  return data;
}

export async function createSuite(
  projectId: number,
  payload: { name: string; description?: string },
): Promise<TestSuite> {
  const { data } = await apiClient.post<TestSuite>(
    `/api/projects/${projectId}/suites`,
    payload,
  );
  return data;
}

export async function updateSuite(
  suiteId: number,
  payload: { name?: string; description?: string },
): Promise<TestSuite> {
  const { data } = await apiClient.put<TestSuite>(`/api/suites/${suiteId}`, payload);
  return data;
}

export async function deleteSuite(suiteId: number): Promise<void> {
  await apiClient.delete(`/api/suites/${suiteId}`);
}
