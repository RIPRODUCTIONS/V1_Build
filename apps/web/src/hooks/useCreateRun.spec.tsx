import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, expect, it } from 'vitest';

import { useCreateRun } from '@/hooks/useCreateRun';
import { useRuns } from '@/hooks/useRuns';

const sharedClient = new QueryClient();
function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={sharedClient}>{children}</QueryClientProvider>;
}

describe('useCreateRun', () => {
  it('optimistically adds a run then refetches', async () => {
    const runs = renderHook(() => useRuns(), { wrapper });
    await waitFor(() => expect(runs.result.current.isSuccess).toBe(true));
    const initial = (runs.result.current.data?.kind === 'list' ? runs.result.current.data.data : runs.result.current.data?.data)?.length ?? 0;

    const create = renderHook(() => useCreateRun(), { wrapper });
    create.result.current.mutate({ title: 'New run' });

                await waitFor(() => {
                  const arr = runs.result.current.data?.kind === 'list' ? runs.result.current.data.data : runs.result.current.data?.data;
                  expect(arr!.length).toBeGreaterThanOrEqual(initial + 1);
                });

    await waitFor(() => expect(runs.result.current.isSuccess).toBe(true));
  });
});
