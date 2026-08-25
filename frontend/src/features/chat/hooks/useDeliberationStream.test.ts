// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { useDeliberationStream } from './useDeliberationStream'
import { useRunStore } from '../../../stores/useRunStore'
import { registerRun } from '../../../api/mock/runsRegistry'

describe('useDeliberationStream', () => {
  beforeEach(() => {
    useRunStore.setState({
      selectedAgents: ['ceo', 'cfo', 'cto', 'cmo'],
      teamModeEnabled: false,
      activeRun: null,
    })
  })

  it('streams mock events into the store and marks the run complete', async () => {
    vi.useFakeTimers()
    try {
      const runId = 'test-run-complete'
      registerRun(runId, {
        prompt: 'test prompt',
        agents: ['ceo', 'cfo', 'cto', 'cmo'],
        teamModeEnabled: false,
      })

      const controller = new AbortController()
      useRunStore.getState().startRun(runId, controller)

      renderHook(() => useDeliberationStream(runId))

      await vi.advanceTimersByTimeAsync(60_000)

      const run = useRunStore.getState().activeRun
      expect(run?.status).toBe('complete')
      expect(run?.events.length).toBeGreaterThan(0)
      expect(run?.events.at(-1)?.type).toBe('synthesis_completed')
    } finally {
      vi.useRealTimers()
    }
  })

  it('stops streaming and freezes the transcript when aborted mid-run', async () => {
    vi.useFakeTimers()
    try {
      const runId = 'test-run-abort'
      registerRun(runId, {
        prompt: 'test prompt',
        agents: ['ceo', 'cfo', 'cto', 'cmo'],
        teamModeEnabled: false,
      })

      const controller = new AbortController()
      useRunStore.getState().startRun(runId, controller)

      renderHook(() => useDeliberationStream(runId))

      await vi.advanceTimersByTimeAsync(400)
      const countBeforeAbort = useRunStore.getState().activeRun?.events.length ?? 0
      expect(countBeforeAbort).toBeGreaterThan(0)

      controller.abort()
      await vi.advanceTimersByTimeAsync(60_000)

      const run = useRunStore.getState().activeRun
      expect(run?.status).toBe('stopped')
      expect(run?.events.length).toBe(countBeforeAbort)
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('useDeliberationStream — server-side failure', () => {
  it('treats error_occurred as terminal so the run stops looking live', async () => {
    // The scripted mock timeline has no failure path, so drive a hand-rolled
    // handle directly rather than trying to make timeline.ts emit an error.
    let emit: ((event: { data: string }) => void) | undefined
    const close = vi.fn()
    const endpoints = await import('../../../api/endpoints')
    const spy = vi.spyOn(endpoints, 'openDeliberationStream').mockReturnValue({
      addEventListener: (type: string, listener: unknown) => {
        if (type === 'message') emit = listener as (event: { data: string }) => void
      },
      close,
    } as unknown as ReturnType<typeof endpoints.openDeliberationStream>)

    try {
      const runId = 'test-run-server-error'
      useRunStore.getState().startRun(runId, new AbortController())
      renderHook(() => useDeliberationStream(runId))

      expect(useRunStore.getState().activeRun?.status).toBe('streaming')

      act(() => {
        emit!({
          data: JSON.stringify({
            type: 'error_occurred',
            error_message: 'LLM provider unreachable',
            phase: 'analysis',
          }),
        })
      })

      expect(useRunStore.getState().activeRun?.status).toBe('error')
    } finally {
      spy.mockRestore()
    }
  })
})
