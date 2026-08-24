import type { CXOName } from '../types'
import type { DeliberationStreamHandle } from '../dto'
import { buildMockTimeline } from './timeline'

export type { DeliberationStreamHandle } from '../dto'

type MessageListener = (event: { data: string }) => void

/**
 * Mimics the subset of the browser EventSource interface that useDeliberationStream needs
 * (addEventListener('message'|'error', ...) + close()), but plays back a scripted timeline on
 * a timer instead of opening a real connection. Paced like the CLI's own `demo` narration
 * (~0.15-0.25s between lines) so the mocked stream feels like watching a real run.
 *
 * The real implementation (api/endpoints.real.ts) wraps an actual `EventSource`, which already
 * satisfies this same shape structurally — see dto.ts.
 */

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
