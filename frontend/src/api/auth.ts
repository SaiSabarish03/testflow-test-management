import { apiClient } from './client';
import type { TokenResponse, User, LoginCredentials } from '../types';

export async function login(
  credentials: LoginCredentials,
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>(
    '/api/auth/login',
    credentials,
  );

  return data;
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/api/auth/me');
  return data;
}
