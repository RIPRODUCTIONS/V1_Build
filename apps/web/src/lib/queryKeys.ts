export const qk = {
  runs: () => ['runs'] as const,
  run: (id: string) => ['run', id] as const,
};
