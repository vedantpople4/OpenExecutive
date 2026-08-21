import type { CXOName } from '../types'
import { buildMockTimeline } from './timeline'

type MessageListener = (event: { data: string }) => void
type ErrorListener = (event: { message: string }) => void

/**
 * Mimics the subset of the browser EventSource interface that useDeliberationStream needs
 * (addEventListener('message'|'error', ...) + close()), but plays back a scripted timeline on
 * a timer instead of opening a real connection. Paced like the CLI's own `demo` narration
 * (~0.15-0.25s between lines) so the mocked stream feels like watching a real run.
 *
 * Swapping to a real backend later means replacing this module's construction site in
 * api/endpoints.ts with `new EventSource(url)` — the hook and every component above it are
 * unaffected because they only depend on this same addEventListener/close shape.
 */
export interface DeliberationStreamHandle {
  addEventListener(type: 'message', listener: MessageListener): void
  addEventListener(type: 'error', listener: ErrorListener): void
  close(): void
}

const MIN_DELAY_MS = 150
const MAX_DELAY_MS = 250

function randomDelay(): number {
  return MIN_DELAY_MS + Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS)
}

export function createMockDeliberationStream(
  runId: string,
  prompt: string,
  agents: CXOName[],
  parentRunId?: string,
): DeliberationStreamHandle {
  const events = buildMockTimeline(runId, prompt, agents, parentRunId)
  const messageListeners: MessageListener[] = []
  let closed = false
  let timer: ReturnType<typeof setTimeout> | null = null

  function scheduleNext(index: number) {
    if (closed) return
    if (index >= events.length) return

    timer = setTimeout(() => {
      if (closed) return
      const event = events[index]
      const data = JSON.stringify(event)
      for (const listener of messageListeners) listener({ data })
      scheduleNext(index + 1)
    }, randomDelay())
  }

  scheduleNext(0)

  return {
    addEventListener(type, listener) {
      if (type === 'message') messageListeners.push(listener as MessageListener)
      // No error path in the mock — the scripted timeline never fails.
    },
    close() {
      closed = true
      if (timer) clearTimeout(timer)
    },
  }
}
