import type { QueryClient } from '@tanstack/react-query';

import { fetchRuns } from '@/lib/api';
import { qk } from '@/lib/queryKeys';

export const prefetchRuns = async (qc: QueryClient) => {
  await qc.prefetchQuery({ queryKey: qk.runs(), queryFn: () => fetchRuns(), staleTime: 30000 });
};
