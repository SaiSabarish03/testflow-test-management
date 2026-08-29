import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { Project, ProjectStatus, PaginatedResponse } from '../types';
import {
  listProjects,
  createProject,
  updateProject,
  archiveProject,
  type UpdateProjectPayload,
} from '../api/projects';

type ProjectQueryParams = {
  search?: string;
  status?: ProjectStatus;
  page?: number;
  page_size?: number;
};

export const projectsQueryKey = (params: ProjectQueryParams = {}) => ['projects', params] as const;

export function useProjects(params: ProjectQueryParams) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery<PaginatedResponse<Project>>({
    queryKey: projectsQueryKey(params),
    queryFn: () => listProjects(params),
    placeholderData: keepPreviousData,
  });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsQueryKey() });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateProjectPayload }) =>
      updateProject(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsQueryKey() });
    },
  });

  const archiveMutation = useMutation({
    mutationFn: archiveProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsQueryKey() });
    },
  });

  return {
    data,
    isLoading,
    error,
    createProject: createMutation.mutateAsync,
    updateProject: updateMutation.mutateAsync,
    archiveProject: archiveMutation.mutateAsync,
  };
}
