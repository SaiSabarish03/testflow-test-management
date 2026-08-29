import { useCallback, useEffect, useRef, useState } from 'react';

interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Minimal hook for async data fetching.
 * Cancels stale updates when the component unmounts or deps change.
 */
export function useAsync<T>(
  fn: () => Promise<T>,
  deps: unknown[],
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    isLoading: true,
    error: null,
  });
  const counter = useRef(0);

  const run = useCallback(() => {
    const id = ++counter.current;
    setState((s) => ({ ...s, isLoading: true, error: null }));
    fn()
      .then((data) => {
        if (id === counter.current) setState({ data, isLoading: false, error: null });
      })
      .catch((err: unknown) => {
        if (id === counter.current) {
          const msg = err instanceof Error ? err.message : 'An error occurred.';
          setState({ data: null, isLoading: false, error: msg });
        }
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { run(); }, [run]);

  return { ...state, reload: run };
}
