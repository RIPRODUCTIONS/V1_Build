import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, expect, it } from 'vitest';

import { useRuns } from '@/hooks/useRuns';

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient();
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('useRuns', () => {
  it('returns mocked runs', async () => {
    const { result } = renderHook(() => useRuns(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const arr = result.current.data?.kind === 'list' ? result.current.data.data : result.current.data?.data;
    expect(arr?.[0].id).toBe('run_1');
  });
});
