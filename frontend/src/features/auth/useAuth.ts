import { useCallback, useEffect, useState } from 'react'
import { API_BASE_URL } from '../../api/client'
import { getSupabaseClient } from '../../api/supabaseClient'

interface AuthState {
  status: 'loading' | 'signedOut' | 'signedIn'
  error: string | null
}

/** Exchanges a freshly-verified Supabase access token for the backend's own HttpOnly session
 * cookie (POST /auth/session, see backend/app/routers/auth.py). Everything downstream —
 * including the SSE stream, which cannot carry an Authorization header — rides on that cookie,
 * never on this token again. */
async function createBackendSession(accessToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/session`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ access_token: accessToken }),
  })
  if (!response.ok) {
    throw new Error('Could not start a session with the server.')
  }
}

// A config error is knowable at mount, so it's a lazy initializer, not a synchronous setState
// inside the effect below (oxlint's react(set-state-in-effect) flags that pattern).
function initialAuthState(): AuthState {
  try {
    getSupabaseClient()
    return { status: 'loading', error: null }
  } catch (err) {
    return {
      status: 'signedOut',
      error: err instanceof Error ? err.message : 'Sign-in is not configured.',
    }
  }
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(initialAuthState)

  useEffect(() => {
    let supabase
    try {
      supabase = getSupabaseClient()
    } catch {
      return // reflected in initialAuthState already
    }

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        setState({ status: 'signedOut', error: null })
        return
      }
      createBackendSession(session.access_token)
        .then(() => setState({ status: 'signedIn', error: null }))
        .catch((err: unknown) => {
          setState({
            status: 'signedOut',
            error: err instanceof Error ? err.message : 'Could not start a session.',
          })
        })
    })
    return () => subscription.unsubscribe()
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await getSupabaseClient().auth.signInWithPassword({ email, password })
    if (error) throw new Error(error.message)
  }, [])

  const signUp = useCallback(async (email: string, password: string) => {
    const { error } = await getSupabaseClient().auth.signUp({ email, password })
    if (error) throw new Error(error.message)
  }, [])

  return { ...state, signIn, signUp }
}
