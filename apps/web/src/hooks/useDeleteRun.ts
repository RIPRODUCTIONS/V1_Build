import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { Run } from '@/contracts/run';
import { deleteRun } from '@/lib/api';
import { toNormalizedError } from '@/lib/errors';
import { qk } from '@/lib/queryKeys';

export function useDeleteRun(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => deleteRun(id),
    onMutate: async () => {
      await qc.cancelQueries({ queryKey: qk.runs() });
      const current = qc.getQueryData(qk.runs());
      const prev: Run[] = Array.isArray((current as any)?.data)
        ? ((current as { data: Run[] }).data)
        : (Array.isArray(current) ? (current as Run[]) : []);
      const next = prev.filter(r => r.id !== id);
      qc.setQueryData(qk.runs(), { kind: 'list', data: next });
      return { prev } as { prev: Run[] };
    },
    onError: (err, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(qk.runs(), { kind: 'list', data: ctx.prev });

      console.error('Delete failed', toNormalizedError(err));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.runs() }),
  });
}
