import type { RegisterSummary } from '../types'

export const mockRegisterSummary: RegisterSummary = {
  total_decisions: 24,
  distinct_prompts: 15,
  total_action_items: 61,
  high_priority_actions: 18,
  top_risks: [
    { text: 'Agent-authored code without strong review gates can erode quality', count: 4 },
    { text: 'Runway impact from funding multiple tracks at once', count: 3 },
    { text: 'Competitive reaction to pricing or positioning changes', count: 2 },
  ],
  agent_alignment: {
    ceo: { mean: 0.86, samples: 24 },
    cfo: { mean: 0.81, samples: 22 },
    cto: { mean: 0.79, samples: 20 },
    cmo: { mean: 0.77, samples: 19 },
  },
  per_month: [
    { month: '2026-06', count: 6 },
    { month: '2026-07', count: 9 },
    { month: '2026-08', count: 9 },
  ],
  most_recent: '20260817_093000',
}
