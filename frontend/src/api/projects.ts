import { apiClient } from './client';
import type { Project, PaginatedResponse } from '../types';

export interface ListProjectsParams {
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function listProjects(params: ListProjectsParams = {}): Promise<PaginatedResponse<Project>> {
  const { data } = await apiClient.get<PaginatedResponse<Project>>('/api/projects', { params });
  return data;
}

export async function getProject(projectId: number): Promise<Project> {
  const { data } = await apiClient.get<Project>(`/api/projects/${projectId}`);
  return data;
}

export interface CreateProjectPayload {
  name: string;
  key: string;
  description?: string;
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  const { data } = await apiClient.post<Project>('/api/projects', payload);
  return data;
}

export interface UpdateProjectPayload {
  name?: string;
  description?: string;
  status?: string;
}

export async function updateProject(projectId: number, payload: UpdateProjectPayload): Promise<Project> {
  const { data } = await apiClient.put<Project>(`/api/projects/${projectId}`, payload);
  return data;
}

export async function archiveProject(projectId: number): Promise<Project> {
  const { data } = await apiClient.delete<Project>(`/api/projects/${projectId}`);
  return data;
}
