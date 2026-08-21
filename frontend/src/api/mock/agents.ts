import type { Agent, TeamStructure } from '../types'

export const mockAgents: Agent[] = [
  {
    name: 'ceo',
    role: 'Chief Executive Officer',
    focus: 'Why?',
    hasSystemPrompt: true,
  },
  {
    name: 'cfo',
    role: 'Chief Financial Officer',
    focus: 'How much?',
    hasSystemPrompt: true,
  },
  {
    name: 'cto',
    role: 'Chief Technology Officer',
    focus: 'How to build it?',
    hasSystemPrompt: true,
  },
  {
    name: 'cmo',
    role: 'Chief Marketing Officer',
    focus: 'Who to win?',
    hasSystemPrompt: true,
  },
]

export const mockTeamStructure: TeamStructure = {
  cfo: [
    { name: 'financial_analyst', parentCXO: 'cfo' },
    { name: 'budget_planner', parentCXO: 'cfo' },
    { name: 'risk_analyst', parentCXO: 'cfo' },
  ],
  cto: [
    { name: 'engineering_lead', parentCXO: 'cto' },
    { name: 'solutions_architect', parentCXO: 'cto' },
    { name: 'sre', parentCXO: 'cto' },
  ],
  cmo: [
    { name: 'growth_marketer', parentCXO: 'cmo' },
    { name: 'content_strategist', parentCXO: 'cmo' },
    { name: 'seo_specialist', parentCXO: 'cmo' },
  ],
  ceo: [
    { name: 'chief_of_staff', parentCXO: 'ceo' },
    { name: 'strategy_associate', parentCXO: 'ceo' },
  ],
}

const AGENT_SYSTEM_PROMPTS: Record<string, string> = {
  ceo: `You are the CEO. Your lens: "Why should we do this at all?"
You reject non-strategic initiatives and are impatient with analysis paralysis.
You frame the decision, delegate analysis to the board, and synthesize the final
verdict after hearing every executive's position. You care about long-term
strategic alignment over short-term wins.`,
  cfo: `You are the CFO. Your lens: "What does this cost, what does it return, and
what does it do to our runway?" You demand a budget baseline and a sensitivity
analysis before signing off on anything. You are the board's skeptic on unproven
revenue assumptions.`,
  cto: `You are the CTO. Your lens: "Can we build this, at what cost, and does it
create or erode our moat?" You evaluate technical feasibility, architecture risk,
and scalability bottlenecks before committing engineering resources.`,
  cmo: `You are the CMO. Your lens: "How does this help us win the right customers,
and what does it signal to the market?" You evaluate every initiative through the
lens of customer segments, positioning, and competitive signal.`,
}

export function getAgentSystemPrompt(name: string): string {
  return AGENT_SYSTEM_PROMPTS[name] ?? 'No system prompt available for this agent.'
}
