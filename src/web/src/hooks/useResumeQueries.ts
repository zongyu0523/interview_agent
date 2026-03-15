import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './queryKeys';
import { fetchResume, parseResume, updateResume } from '../services/api';
import type { ResumeData } from '../types/resume';

export function useResume() {
  return useQuery({
    queryKey: queryKeys.resume.detail(),
    queryFn: fetchResume,
    staleTime: Infinity,
  });
}

export function useParseResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => parseResume(file),
    onSuccess: (data: ResumeData) => {
      queryClient.setQueryData(queryKeys.resume.detail(), data);
    },
  });
}

export function useUpdateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateResume>[0]) => updateResume(data),
    onSuccess: (data: ResumeData) => {
      queryClient.setQueryData(queryKeys.resume.detail(), data);
    },
  });
}
