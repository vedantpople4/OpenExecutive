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
      // Terminal too: without this the run sits at 'streaming' forever, so the
      // stop button and streaming indicator persist on a run that already died.
      if (parsed.type === 'error_occurred') setRunStatus('error')
    }

    function handleError() {
      // Close before flipping status. A real EventSource reconnects on its own after any
      // transport error and the backend replays the whole stored history from the top on
      // every connect (no Last-Event-ID handling in backend/app/routers/events.py), so
      // leaving it open means an endless reconnect loop underneath a UI that already says
      // the run failed. The dedup guard in useRunStore stops that loop from duplicating
      // cards, but only closing stops the requests -- and only a closed stream can be
      // safely replaced by a retry.
      stream.close()
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
