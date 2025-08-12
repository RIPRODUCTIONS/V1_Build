export type NormalizedError = {
  code: string;
  message: string;
  status?: number;
  cause?: unknown;
};

export function toNormalizedError(
  input: unknown,
  fallback: Partial<NormalizedError> = {},
): NormalizedError {
  if (
    input &&
    typeof input === 'object' &&
    'name' in input &&
    (input as { name?: unknown }).name === 'HttpError'
  ) {
    const err = input as unknown as { message?: string; status?: number; body?: unknown };
    const code = err.status ? `HTTP_${err.status}` : 'HTTP_ERROR';
    let message: string | undefined;
    if (err.body && typeof err.body === 'object' && 'message' in err.body) {
      const msg = (err.body as { message?: unknown }).message;
      if (typeof msg === 'string') message = msg;
    }
    message = message || err.message || 'Request failed';
    return { code, message, status: err.status, cause: err };
  }

  if (input instanceof Error) {
    return { code: 'ERROR', message: input.message || 'Unknown error', cause: input };
  }

  if (typeof input === 'string') {
    return { code: 'ERROR', message: input };
  }

  return {
    code: fallback.code || 'ERROR',
    message: fallback.message || 'Something went wrong',
    status: fallback.status,
    cause: input,
  };
}
