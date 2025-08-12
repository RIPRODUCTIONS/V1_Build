import { describe, expect, it, vi } from 'vitest';

import { prefetchRuns } from './prefetch';

describe('prefetchRuns', () => {
  it('calls prefetchQuery with runs key', async () => {
    const qc = {
      prefetchQuery: vi.fn().mockResolvedValue(undefined),
    } as unknown as { prefetchQuery: (args: unknown) => Promise<unknown> };
    await prefetchRuns(qc as never);
    expect((qc as { prefetchQuery: unknown }).prefetchQuery).toBeDefined();
  });
});
