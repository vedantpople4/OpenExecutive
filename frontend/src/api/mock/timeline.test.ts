import { describe, expect, it } from 'vitest'
import { buildMockTimeline } from './timeline'
import type { AgentSpeakingEvent, DeliberationEvent } from '../types'

function isAgentSpeaking(event: DeliberationEvent): event is AgentSpeakingEvent {
  return event.type === 'agent_speaking'
}

describe('buildMockTimeline', () => {
  it('starts with simulation_initialized and ends with synthesis_completed', () => {
    const events = buildMockTimeline('run-test', 'test prompt', ['ceo', 'cfo', 'cto', 'cmo'])
    expect(events[0].type).toBe('simulation_initialized')
    expect(events[events.length - 1].type).toBe('synthesis_completed')
  })

  it('pairs every deliberation_round_started with a deliberation_round_completed', () => {
    const events = buildMockTimeline('run-test', 'test prompt', ['ceo', 'cfo', 'cto', 'cmo'])
    const started = events.filter((e) => e.type === 'deliberation_round_started').length
    const completed = events.filter((e) => e.type === 'deliberation_round_completed').length
    expect(started).toBe(completed)
    expect(started).toBeGreaterThan(0)
  })

  it('only emits analysis-phase reports for agents in the requested selection', () => {
    const events = buildMockTimeline('run-test', 'test prompt', ['ceo', 'cfo'])
    const analysisSpeakingAgents = events
      .filter(isAgentSpeaking)
      .filter((e) => e.round_number === undefined)
      .map((e) => e.agent_name)
    expect(analysisSpeakingAgents).toEqual(['ceo', 'cfo'])
  })

  it('gives every event a unique event_id', () => {
    const events = buildMockTimeline('run-test', 'test prompt', ['ceo', 'cfo', 'cto', 'cmo'])
    const ids = new Set(events.map((e) => e.event_id))
    expect(ids.size).toBe(events.length)
  })
})
