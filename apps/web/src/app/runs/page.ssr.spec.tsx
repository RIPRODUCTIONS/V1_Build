import { describe, expect, it } from 'vitest';

describe('runs page SSR', () => {
  it('server module loads without throwing', async () => {
    const mod = await import('./page');
    expect(mod.default).toBeTypeOf('function');
  });
});
