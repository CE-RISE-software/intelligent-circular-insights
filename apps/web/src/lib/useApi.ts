import { useCallback, useEffect, useRef, useState } from "react";
import type { ApiResult } from "./api";
import { getRequestedMode, subscribe } from "./mode";

/**
 * Run a request, keep its outcome, and re-run it when the mode changes.
 *
 * The mode dependency is the point: switching backend has to re-fetch every
 * window, otherwise the page shows Normal-mode numbers under a CE-RISE badge.
 */
export function useApi<T>(
  fn: () => Promise<ApiResult<T>>,
  deps: readonly unknown[] = [],
  options: { immediate?: boolean } = {},
): {
  result: ApiResult<T> | null;
  pending: boolean;
  run: () => void;
} {
  const immediate = options.immediate ?? true;
  const [result, setResult] = useState<ApiResult<T> | null>(null);
  const [pending, setPending] = useState(immediate);
  const [modeTick, setModeTick] = useState(0);
  const latest = useRef(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => subscribe(() => setModeTick(t => t + 1)), []);

  const run = useCallback(() => {
    const ticket = ++latest.current;
    setPending(true);
    void fnRef.current().then(r => {
      // Late responses from a superseded request are discarded rather than
      // painted over a newer one.
      if (ticket !== latest.current) return;
      setResult(r);
      setPending(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!immediate) return;
    run();
    // Re-runs on the caller's deps and on any mode change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, modeTick, immediate]);

  return { result, pending, run };
}

/** The current requested mode as a reactive value. */
export function useRequestedMode() {
  const [mode, setMode] = useState(getRequestedMode);
  useEffect(() => subscribe(() => setMode(getRequestedMode())), []);
  return mode;
}
