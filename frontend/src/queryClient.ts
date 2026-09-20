import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from './api/client'
import { router } from './routes/router'

export function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403)
}

/** A session that's expired or was never there looks the same everywhere: send the user to
 * /login. This runs once per request via the cache-level callback (not per-observer, which
 * TanStack Query v5 dropped for exactly this kind of side effect) rather than duplicated in
 * every hook, and skips it if already there so a query firing on the login page itself can't
 * loop. */
function redirectToLoginOn401(error: unknown) {
  if (isAuthError(error) && router.state.location.pathname !== '/login') {
    void router.navigate('/login')
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // No point burning the default 3 retries against a 401/403 -- it won't resolve itself.
      retry: (failureCount, error) => !isAuthError(error) && failureCount < 3,
    },
  },
  queryCache: new QueryCache({ onError: redirectToLoginOn401 }),
  mutationCache: new MutationCache({ onError: redirectToLoginOn401 }),
})
