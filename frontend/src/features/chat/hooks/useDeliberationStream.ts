import { useEffect } from 'react'
import { openDeliberationStream } from '../../../api/endpoints'
import { useRunStore } from '../../../stores/useRunStore'
import type { DeliberationEvent } from '../../../api/types'

/**
 * Owns the streaming connection lifecycle for one run (connect/parse/append/close). No card
 * component ever touches the stream directly — they only read `activeRun.events` off the store.
 * Backed by a mocked SSE-like player today (src/api/mock/mockEventSource.ts); swapping to a real
 * `EventSource` later only changes what `openDeliberationStream` returns, not this hook.
 */
export function useDeliberationStream(runId: string | null): void {
  const appendEvent = useRunStore((state) => state.appendEvent)
  const setRunStatus = useRunStore((state) => state.setRunStatus)

  useEffect(() => {
    if (!runId) return

    const controller = useRunStore.getState().activeRun?.abortController
    if (!controller) return

    const stream = openDeliberationStream(runId)
    setRunStatus('streaming')

    function handleMessage(event: { data: string }) {
      const parsed = JSON.parse(event.data) as DeliberationEvent
      appendEvent(parsed)
      if (parsed.type === 'synthesis_completed') setRunStatus('complete')
    }

    function handleError() {
      setRunStatus('error')
    }

    function handleAbort() {
      stream.close()
      setRunStatus('stopped')
    }

    stream.addEventListener('message', handleMessage)
    stream.addEventListener('error', handleError)
    controller.signal.addEventListener('abort', handleAbort)

    return () => {
      stream.close()
      controller.signal.removeEventListener('abort', handleAbort)
    }
  }, [runId, appendEvent, setRunStatus])
}
