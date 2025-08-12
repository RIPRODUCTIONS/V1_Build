import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, expect, it } from 'vitest';

import { useDeleteRun } from '@/hooks/useDeleteRun';
import { useRuns } from '@/hooks/useRuns';

const shared = new QueryClient();
function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={shared}>{children}</QueryClientProvider>;
}

describe('useDeleteRun', () => {
  it('optimistically removes item then refetches', async () => {
    const runs = renderHook(() => useRuns(), { wrapper });
    await waitFor(() => expect(runs.result.current.isSuccess).toBe(true));
    const arr0 = runs.result.current.data?.kind === 'list' ? runs.result.current.data.data : runs.result.current.data?.data!;
    const initial = arr0.length;
    const id = arr0[0].id;

    const del = renderHook(() => useDeleteRun(id), { wrapper });
    del.result.current.mutate();

    await waitFor(() => {
      const arr = runs.result.current.data?.kind === 'list' ? runs.result.current.data.data : runs.result.current.data?.data!;
      expect(arr.length).toBeLessThan(initial);
    });
  });
});
