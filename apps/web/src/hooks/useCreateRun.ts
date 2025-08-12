import { useMutation, useQueryClient } from '@tanstack/react-query';

import { createRun } from '@/lib/api';
import { toNormalizedError } from '@/lib/errors';
import { qk } from '@/lib/queryKeys';
import type { CreateRunInputT, Run } from '@/types/run';

export function useCreateRun() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateRunInputT) => createRun(input),
    onMutate: async input => {
      await qc.cancelQueries({ queryKey: qk.runs() });
      const current = qc.getQueryData(qk.runs());
      const prev: Run[] = Array.isArray((current as any)?.data)
        ? ((current as { data: Run[] }).data)
        : (Array.isArray(current) ? (current as Run[]) : []);
      const optimistic: Run = {
        id: `optimistic_${Date.now()}`,
        status: 'queued',
        startedAt: new Date().toISOString(),
        finishedAt: null,
        title: input.title,
      };
      const nextArray = [optimistic, ...prev];
      qc.setQueryData(qk.runs(), { kind: 'list', data: nextArray });
      return { prev } as { prev: Run[] };
    },
    onError: (error, _input, ctx) => {
      if (ctx?.prev) qc.setQueryData(qk.runs(), { kind: 'list', data: ctx.prev });
      const nerr = toNormalizedError(error);

      console.error('Create run failed', nerr);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.runs() });
    },
  });
}
