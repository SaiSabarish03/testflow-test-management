import { apiClient } from './client';
import type { User, PaginatedResponse } from '../types';

export interface ListUsersParams {
  search?: string;
  role?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export async function listUsers(params: ListUsersParams = {}): Promise<PaginatedResponse<User>> {
  const { data } = await apiClient.get<PaginatedResponse<User>>('/api/users', { params });
  return data;
}

export async function getUser(userId: number): Promise<User> {
  const { data } = await apiClient.get<User>(`/api/users/${userId}`);
  return data;
}

export interface CreateUserPayload {
  name: string;
  email: string;
  password: string;
  role: string;
}

export async function createUser(payload: CreateUserPayload): Promise<User> {
  const { data } = await apiClient.post<User>('/api/users', payload);
  return data;
}

export interface UpdateUserPayload {
  name?: string;
  email?: string;
  role?: string;
  status?: string;
}

export async function updateUser(userId: number, payload: UpdateUserPayload): Promise<User> {
  const { data } = await apiClient.put<User>(`/api/users/${userId}`, payload);
  return data;
}

export async function deactivateUser(userId: number): Promise<User> {
  const { data } = await apiClient.delete<User>(`/api/users/${userId}`);
  return data;
}
