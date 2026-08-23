/**
 * Request/response DTOs and client-side transport contracts shared between the mock and real
 * implementations of endpoints.ts, so both stay structurally forced to agree on the same shape.
 */
import type { CXOName } from './types'

export interface SubmitPromptRequest {
  prompt: string
  agents: CXOName[]
  teamModeEnabled: boolean
  parentRunId?: string
}

export interface SubmitPromptResponse {
  runId: string
}

type MessageListener = (event: { data: string }) => void
type ErrorListener = (event: { message: string }) => void

/**
 * The subset of the browser EventSource interface useDeliberationStream needs. A real
 * `EventSource` already satisfies this shape structurally — see api/endpoints.real.ts.
 */
export interface DeliberationStreamHandle {
  addEventListener(type: 'message', listener: MessageListener): void
  addEventListener(type: 'error', listener: ErrorListener): void
  close(): void
}
