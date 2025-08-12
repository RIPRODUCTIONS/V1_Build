import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, expect, it } from 'vitest';

import { useRuns } from '@/hooks/useRuns';
import { useUpdateRun } from '@/hooks/useUpdateRun';

const shared = new QueryClient();
function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={shared}>{children}</QueryClientProvider>;
}

describe('useUpdateRun', () => {
  it('optimistically updates title then refetches', async () => {
    const runs = renderHook(() => useRuns(), { wrapper });
    await waitFor(() => expect(runs.result.current.isSuccess).toBe(true));

    const arr0 = runs.result.current.data?.kind === 'list' ? runs.result.current.data.data : runs.result.current.data?.data!;
    const id = arr0[0].id;
    const upd = renderHook(() => useUpdateRun(id), { wrapper });
    upd.result.current.mutate({ title: 'Renamed' });

    await waitFor(() => {
      const arr = runs.result.current.data?.kind === 'list' ? runs.result.current.data.data : runs.result.current.data?.data!;
      const item = arr.find((r: { id: string }) => r.id === id)!;
      expect((item as { title: string }).title).toContain('Renamed');
    });
  });
});
