"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Options<T> = {
  key: unknown[];
  fetchPage: (_args: { offset: number; limit: number }) => Promise<T[]>;
  pageSize?: number;
};

export function usePagedList<T>({ key, fetchPage, pageSize = 20 }: Options<T>) {
  const depsKey = useMemo(() => JSON.stringify(key), [key]);
  const [items, setItems] = useState<T[]>([]);
  const [offset, setOffset] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  async function load(reset: boolean) {
    try {
      setError(null);
      const data = await fetchPage({ offset: reset ? 0 : offset, limit: pageSize });
      setItems((prev) => (reset ? data : [...prev, ...data]));
      if (!reset && data.length > 0) setOffset((v) => v + pageSize);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    }
  }

  useEffect(() => {
    setOffset(0);
    void load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [depsKey]);

  useEffect(() => {
    const ob = new IntersectionObserver(async (entries) => {
      if (entries[0]?.isIntersecting && !loadingMore) {
        setLoadingMore(true);
        try {
          await load(false);
        } finally {
          setLoadingMore(false);
        }
      }
    });
    if (sentinelRef.current) ob.observe(sentinelRef.current);
    return () => ob.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadingMore, offset, depsKey]);

  return { items, loadingMore, error, sentinelRef, reset: () => load(true) } as const;
}
