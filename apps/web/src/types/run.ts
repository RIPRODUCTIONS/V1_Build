import { z } from 'zod';

export const RunSchema = z.object({
  id: z.string(),
  status: z.enum(['queued', 'running', 'failed', 'success']),
  startedAt: z.string().datetime(),
  finishedAt: z.string().datetime().nullable(),
  title: z.string().min(1).default('Untitled'),
});

export const RunsSchema = z.array(RunSchema);

export const CreateRunInput = z.object({
  title: z.string().min(1, 'Title is required'),
});

export const CreateRunResult = RunSchema;

export type Run = z.infer<typeof RunSchema>;
export type CreateRunInputT = z.infer<typeof CreateRunInput>;
