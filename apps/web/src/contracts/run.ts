import { z } from 'zod';

export const RunId = z.string().min(1);

export const RunSchema = z.object({
  id: RunId,
  status: z.enum(['queued', 'running', 'failed', 'success']),
  startedAt: z.string().datetime(),
  finishedAt: z.string().datetime().nullable(),
  title: z.string().min(1),
});

export const RunsSchema = z.array(RunSchema);

export const RunsPageSchema = z.object({
  data: RunsSchema,
  page: z.number().int().min(1),
  pageSize: z.number().int().min(1),
  total: z.number().int().min(0),
});

export type RunsPage = z.infer<typeof RunsPageSchema>;

export const CreateRunInput = z.object({
  title: z.string().min(1, 'Title is required'),
});

export const UpdateRunInput = z.object({
  title: z.string().min(1).optional(),
  status: z.enum(['queued', 'running', 'failed', 'success']).optional(),
});

export type Run = z.infer<typeof RunSchema>;
export type CreateRunInputT = z.infer<typeof CreateRunInput>;
export type UpdateRunInputT = z.infer<typeof UpdateRunInput>;
