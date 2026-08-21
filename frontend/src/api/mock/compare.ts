import type { CompareResult } from '../types'

export const mockCompareResult: CompareResult = {
  old_prompt: 'Should we hire more Software Engineers or build AI agents to do the work?',
  new_prompt: 'The AI-agent pilot from two weeks ago is showing a 40% throughput gain with no defect-rate increase — should we expand it?',
  same_prompt: false,
  old_summary: 'Hybrid approach: fund a bounded AI-agent pilot before committing to additional headcount.',
  new_summary: 'Expand the pilot; hold the hiring decision one more cycle.',
  consensus_added: ['Expand pilot scope to two more backlog categories.'],
  consensus_removed: ['No external messaging during the pilot.'],
  dissent_added: [],
  dissent_removed: ['CTO flagged the 6-week window as tight for a confident reliability signal.'],
  actions_added: ['Expand pilot to code-review-assist tasks'],
  actions_removed: ['Launch AI-agent pilot on test coverage backlog'],
  risks_added: ['Scope creep on the pilot without re-tightening the kill criterion.'],
  risks_removed: [],
  agent_scores: [
    { agent: 'ceo', old: 0.88, new: 0.87, delta: -0.01 },
    { agent: 'cfo', old: 0.82, new: 0.86, delta: 0.04 },
    { agent: 'cto', old: 0.79, new: null, delta: null },
    { agent: 'cmo', old: 0.75, new: null, delta: null },
  ],
}
