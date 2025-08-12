import type { QueryClient } from '@tanstack/react-query';

type Ctx<T> = { prev?: T };

export function optimisticListUpdate<TItem extends { id: string }>(
  qc: QueryClient,
  key: readonly unknown[],
  id: string,
  patch: Partial<TItem>,
) {
  const prev = qc.getQueryData<TItem[]>(key) || [];
  const next = prev.map(item => (item.id === id ? ({ ...item, ...patch } as TItem) : item));
  qc.setQueryData(key, next);
  return { prev } as Ctx<TItem[]>;
}

export function optimisticListDelete<TItem extends { id: string }>(
  qc: QueryClient,
  key: readonly unknown[],
  id: string,
) {
  const prev = qc.getQueryData<TItem[]>(key) || [];
  const next = prev.filter(item => item.id !== id) as TItem[];
  qc.setQueryData(key, next);
  return { prev } as Ctx<TItem[]>;
}

export function rollback<T>(qc: QueryClient, key: readonly unknown[], ctx?: Ctx<T>) {
  if (ctx?.prev) qc.setQueryData(key, ctx.prev);
}
