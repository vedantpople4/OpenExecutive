// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useAuth } from './useAuth'
import { getSupabaseClient } from '../../api/supabaseClient'

vi.mock('../../api/supabaseClient', () => ({ getSupabaseClient: vi.fn() }))
const getSupabaseClientMock = vi.mocked(getSupabaseClient)

type AuthChangeCallback = (event: string, session: { access_token: string } | null) => void

function makeFakeSupabase() {
  let onChange: AuthChangeCallback = () => {}
  const unsubscribe = vi.fn()
  return {
    fireAuthChange: (session: { access_token: string } | null) => onChange('SIGNED_IN', session),
    unsubscribe,
    client: {
      auth: {
        onAuthStateChange: vi.fn((cb: AuthChangeCallback) => {
          onChange = cb
          return { data: { subscription: { unsubscribe } } }
        }),
        signInWithPassword: vi.fn(),
        signUp: vi.fn(),
      },
    },
  }
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('reports signedOut immediately when Supabase is not configured', async () => {
    getSupabaseClientMock.mockImplementation(() => {
      throw new Error('VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set to sign in.')
    })

    const { result } = renderHook(() => useAuth())

    await waitFor(() => expect(result.current.status).toBe('signedOut'))
    expect(result.current.error).toMatch(/must be set to sign in/)
  })

  it('exchanges a Supabase session for the backend cookie and reports signedIn', async () => {
    const fake = makeFakeSupabase()
    getSupabaseClientMock.mockReturnValue(fake.client as never)
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 200 }))

    const { result } = renderHook(() => useAuth())
    fake.fireAuthChange({ access_token: 'a-supabase-jwt' })

    await waitFor(() => expect(result.current.status).toBe('signedIn'))
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/session'),
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ access_token: 'a-supabase-jwt' }),
      }),
    )
  })

  it('stays signedOut and surfaces the error when the backend rejects the token', async () => {
    const fake = makeFakeSupabase()
    getSupabaseClientMock.mockReturnValue(fake.client as never)
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 401 }))

    const { result } = renderHook(() => useAuth())
    fake.fireAuthChange({ access_token: 'a-bad-jwt' })

    await waitFor(() => expect(result.current.status).toBe('signedOut'))
    expect(result.current.error).toMatch(/Could not start a session/)
  })

  it('reports signedOut when Supabase reports no session', async () => {
    const fake = makeFakeSupabase()
    getSupabaseClientMock.mockReturnValue(fake.client as never)

    const { result } = renderHook(() => useAuth())
    fake.fireAuthChange(null)

    await waitFor(() => expect(result.current.status).toBe('signedOut'))
    expect(result.current.error).toBeNull()
  })

  it('unsubscribes on unmount', () => {
    const fake = makeFakeSupabase()
    getSupabaseClientMock.mockReturnValue(fake.client as never)

    const { unmount } = renderHook(() => useAuth())
    unmount()

    expect(fake.unsubscribe).toHaveBeenCalled()
  })

  it('signIn rejects with the Supabase error message', async () => {
    const fake = makeFakeSupabase()
    fake.client.auth.signInWithPassword.mockResolvedValue({
      data: {},
      error: { message: 'Invalid login credentials' },
    })
    getSupabaseClientMock.mockReturnValue(fake.client as never)

    const { result } = renderHook(() => useAuth())

    await expect(result.current.signIn('a@b.com', 'pw')).rejects.toThrow(
      'Invalid login credentials',
    )
  })
})
