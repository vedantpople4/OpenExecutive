import { describe, expect, it, beforeEach } from 'vitest'
import { useRunStore } from './useRunStore'

describe('useRunStore', () => {
  beforeEach(() => {
    useRunStore.setState({
      selectedAgents: ['ceo', 'cfo', 'cto', 'cmo'],
      teamModeEnabled: false,
      activeRun: null,
    })
  })

  it('toggles an agent out of and back into selection', () => {
    useRunStore.getState().toggleAgent('cmo')
    expect(useRunStore.getState().selectedAgents).not.toContain('cmo')

    useRunStore.getState().toggleAgent('cmo')
    expect(useRunStore.getState().selectedAgents).toContain('cmo')
  })

  it('keeps canonical CEO/CFO/CTO/CMO order after toggling an agent off and back on', () => {
    useRunStore.getState().toggleAgent('ceo')
    useRunStore.getState().toggleAgent('ceo')
    expect(useRunStore.getState().selectedAgents).toEqual(['ceo', 'cfo', 'cto', 'cmo'])
  })

  it('increments resetSignal on resetActiveRun so consumers can detect an explicit reset', () => {
    const before = useRunStore.getState().resetSignal
    useRunStore.getState().resetActiveRun()
    expect(useRunStore.getState().resetSignal).toBe(before + 1)
    expect(useRunStore.getState().activeRun).toBeNull()
  })

  it('starts a run and appends events without mutating prior state', () => {
    const controller = new AbortController()
    useRunStore.getState().startRun('run-1', controller)

    const event = {
      event_id: 'e1',
      timestamp: new Date().toISOString(),
      aggregate_id: 'run-1',
      type: 'simulation_initialized' as const,
      core_prompt: 'test',
      decision_point: null,
      agent_names: ['ceo'],
    }
    useRunStore.getState().appendEvent(event)

    const run = useRunStore.getState().activeRun
    expect(run?.events).toHaveLength(1)
    expect(run?.status).toBe('connecting')

    useRunStore.getState().setRunStatus('streaming')
    expect(useRunStore.getState().activeRun?.status).toBe('streaming')
  })

  it('ignores an event it has already seen, so an EventSource reconnect cannot duplicate cards', () => {
    useRunStore.getState().startRun('run-1', new AbortController())

    const event = {
      event_id: 'e1',
      timestamp: new Date().toISOString(),
      aggregate_id: 'run-1',
      type: 'simulation_initialized' as const,
      core_prompt: 'test',
      decision_point: null,
      agent_names: ['ceo'],
    }

    // EventSource reconnects by itself and the backend replays from the top, so the same
    // event genuinely arrives twice in production -- not a hypothetical.
    useRunStore.getState().appendEvent(event)
    useRunStore.getState().appendEvent(event)

    expect(useRunStore.getState().activeRun?.events).toHaveLength(1)
  })

  it('keeps events that carry no event_id rather than collapsing them into one', () => {
    useRunStore.getState().startRun('run-1', new AbortController())

    // to_wire_event() in backend/app/routers/events.py defaults a missing event_id to ''.
    const base = {
      event_id: '',
      timestamp: new Date().toISOString(),
      aggregate_id: 'run-1',
      type: 'agent_speaking' as const,
    }
    useRunStore.getState().appendEvent({ ...base, agent_name: 'ceo' })
    useRunStore.getState().appendEvent({ ...base, agent_name: 'cfo' })

    expect(useRunStore.getState().activeRun?.events).toHaveLength(2)
  })
})
