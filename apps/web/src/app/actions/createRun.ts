'use server';

import { z } from 'zod';

import { CreateRunResult } from '@/types/run';

// Demo Zod-validated server action
export async function createRunAction(formData: FormData) {
  const schema = z.object({ title: z.string().min(1) });
  const parsed = schema.safeParse({ title: formData.get('title') });
  if (!parsed.success) {
    return {
      ok: false as const,
      error: parsed.error.flatten().fieldErrors.title?.[0] ?? 'Invalid input',
    };
  }

  const fake = {
    id: `run_${Date.now()}`,
    status: 'queued' as const,
    startedAt: new Date().toISOString(),
    finishedAt: null,
    title: parsed.data.title,
  };

  const checked = CreateRunResult.parse(fake);
  return { ok: true as const, data: checked };
}
