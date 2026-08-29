import { apiClient } from './client';
import type { Defect, PaginatedResponse } from '../types';

export interface ListDefectsParams {
  project_id?: number;
  test_case_id?: number;
  severity?: string;
  priority?: string;
  status?: string;
  assigned_to?: number;
  search?: string;
  page?: number;
  page_size?: number;
}

export async function listDefects(params: ListDefectsParams = {}): Promise<PaginatedResponse<Defect>> {
  const { data } = await apiClient.get<PaginatedResponse<Defect>>('/api/defects', { params });
  return data;
}

export async function getDefect(defectId: number): Promise<Defect> {
  const { data } = await apiClient.get<Defect>(`/api/defects/${defectId}`);
  return data;
}

export interface CreateDefectPayload {
  project_id: number;
  test_case_id?: number;
  title: string;
  description?: string;
  severity: string;
  priority: string;
  environment?: string;
  assigned_to?: number;
}

export async function createDefect(payload: CreateDefectPayload): Promise<Defect> {
  const { data } = await apiClient.post<Defect>('/api/defects', payload);
  return data;
}

export interface UpdateDefectPayload {
  title?: string;
  description?: string;
  severity?: string;
  priority?: string;
  environment?: string;
  assigned_to?: number;
  status?: string;
}

export async function updateDefect(defectId: number, payload: UpdateDefectPayload): Promise<Defect> {
  const { data } = await apiClient.put<Defect>(`/api/defects/${defectId}`, payload);
  return data;
}

export async function deleteDefect(defectId: number): Promise<void> {
  await apiClient.delete(`/api/defects/${defectId}`);
}
