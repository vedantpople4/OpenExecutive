import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import { SUPABASE_ANON_KEY, SUPABASE_URL } from './client'

let client: SupabaseClient | undefined

/** Lazy singleton so importing this module (e.g. transitively, in a test that never signs in)
 * never requires the env vars — only actually calling this does. */
export function getSupabaseClient(): SupabaseClient {
  if (!client) {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      throw new Error('VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set to sign in.')
    }
    client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  }
  return client
}
