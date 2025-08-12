import { QueryClient } from '@tanstack/react-query';

export function getServerQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: 0 } },
  });
}
