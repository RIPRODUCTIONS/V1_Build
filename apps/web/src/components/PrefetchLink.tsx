'use client';

import { useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useEffect, useRef } from 'react';

type PrefetchFn = (qc: ReturnType<typeof useQueryClient>) => Promise<unknown> | unknown;

type Props = React.ComponentProps<typeof Link> & {
  prefetch?: PrefetchFn;
  prefetchOnVisible?: boolean;
};

export default function PrefetchLink({ prefetch, prefetchOnVisible = true, ...props }: Props) {
  const qc = useQueryClient();
  const ref = useRef<HTMLAnchorElement | null>(null);

  useEffect(() => {
    if (!prefetchOnVisible || !ref.current || !prefetch) return;
    const el = ref.current;
    let observer: IntersectionObserver | null = new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) {
        prefetch(qc);
        observer?.disconnect();
        observer = null;
      }
    });
    observer.observe(el);
    return () => observer?.disconnect();
  }, [prefetchOnVisible, prefetch, qc]);

  return (
    <Link
      {...props}
      ref={node => {
        ref.current = node;
      }}
      onMouseEnter={e => {
        props.onMouseEnter?.(e);
        if (prefetch) prefetch(qc);
      }}
    />
  );
}
