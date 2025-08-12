import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { Run } from '@/contracts/run';
import { updateRun } from '@/lib/api';
import { toNormalizedError } from '@/lib/errors';
import { qk } from '@/lib/queryKeys';

export function useUpdateRun(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<Run>) => updateRun(id, patch),
    onMutate: async patch => {
      await qc.cancelQueries({ queryKey: qk.runs() });
      const current = qc.getQueryData(qk.runs());
      const prev: Run[] = Array.isArray((current as any)?.data)
        ? ((current as { data: Run[] }).data)
        : (Array.isArray(current) ? (current as Run[]) : []);
      const next = prev.map(r => (r.id === id ? ({ ...r, ...patch } as Run) : r));
      qc.setQueryData(qk.runs(), { kind: 'list', data: next });
      return { prev } as { prev: Run[] };
    },
    onError: (err, _patch, ctx) => {
      if (ctx?.prev) qc.setQueryData(qk.runs(), { kind: 'list', data: ctx.prev });

      console.error('Update failed', toNormalizedError(err));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.runs() }),
  });
}
