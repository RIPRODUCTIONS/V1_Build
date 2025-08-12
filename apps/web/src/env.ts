export const env = {
  NEXT_PUBLIC_API_BASE:
    process.env.NEXT_PUBLIC_API_BASE || (typeof window === 'undefined' ? '' : ''),
};

import { z } from 'zod';

const serverSchema = z.object({
  DATABASE_URL: z.string().min(1).optional(),
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  NEXTAUTH_SECRET: z.string().min(1).optional(),
});

const clientSchema = z.object({
  NEXT_PUBLIC_MOCK: z.enum(['true', 'false']).default('false'),
});

export const env = {
  ...serverSchema.parse(process.env),
  ...clientSchema.parse({ NEXT_PUBLIC_MOCK: process.env.NEXT_PUBLIC_MOCK ?? 'false' }),
};

if (env.NODE_ENV === 'production' && !env.DATABASE_URL) {
  throw new Error('DATABASE_URL is required in production');
}
