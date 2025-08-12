import { useQuery } from '@tanstack/react-query';
import type { z } from 'zod';

import { RunsSchema } from '@/contracts/run';
import { fetchRuns } from '@/lib/api';
import { qk } from '@/lib/queryKeys';

export function useRuns(params?: {
  page?: number;
  pageSize?: number;
  status?: 'queued' | 'running' | 'failed' | 'success';
}) {
  const key = params?.page || params?.pageSize || params?.status ? [qk.runs(), params] : qk.runs();
  return useQuery<{ kind: 'list'; data: z.infer<typeof RunsSchema> } | { kind: 'page'; data: z.infer<typeof RunsSchema>; page: number; pageSize: number; total: number }>({
    queryKey: key,
    queryFn: () => fetchRuns(params),
    staleTime: 5000,
  });
}
