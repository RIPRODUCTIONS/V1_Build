import { describe, expect, it } from 'vitest';

import * as svc from './runs.service';

describe('runs.service', () => {
  it('listRuns returns array', async () => {
    const runs = await svc.listRuns();
    expect(Array.isArray(runs)).toBe(true);
  });
});
