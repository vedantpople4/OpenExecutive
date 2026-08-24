import type { Agent, DecisionDetail, TeamStructure } from './types'
import type {
  SubmitPromptRequest,
  SubmitPromptResponse,
  StopDecisionResponse,
  GetDecisionHistoryParams,
  DecisionHistoryPage,
  DeliberationStreamHandle,
} from './dto'
import { mockDelay } from './client'
import { mockAgents, mockTeamStructure, getAgentSystemPrompt as mockGetAgentSystemPrompt } from './mock/agents'
import { mockDecisionDetails, mockDecisionHistory } from './mock/decisions'
import { mockCompareResult } from './mock/compare'
import { mockRegisterSummary } from './mock/dashboard'
import { createMockDeliberationStream } from './mock/mockEventSource'
import { getRunConfig, registerRun } from './mock/runsRegistry'
import type { CompareResult, RegisterSummary } from './types'

export function getAgents(): Promise<Agent[]> {
  return mockDelay(mockAgents)
}

export function getTeamStructure(): Promise<TeamStructure> {
  return mockDelay(mockTeamStructure)
}

export function getAgentSystemPrompt(agentName: string): Promise<string> {
  return mockDelay(mockGetAgentSystemPrompt(agentName))
}

/** Simulates real cursor pagination over the fixture list, so "load more" is exercisable
 * against mocks — filters by q, then slices by a plain numeric-offset cursor (only round-tripped
 * by the frontend, unlike the backend's opaque base64 DynamoDB key, so no need to mimic that). */
export function getDecisionHistory(params: GetDecisionHistoryParams = {}): Promise<DecisionHistoryPage> {
  const { q, cursor, limit = 20 } = params
  let items = mockDecisionHistory
  if (q) {
    const needle = q.toLowerCase()
    items = items.filter((d) => d.prompt.toLowerCase().includes(needle))
  }
  const start = cursor ? Number(cursor) : 0
  const page = items.slice(start, start + limit)
  const nextCursor = start + limit < items.length ? String(start + limit) : null
  return mockDelay({ items: page, nextCursor })
}

export function getDecisionDetail(runId: string): Promise<DecisionDetail> {
  const detail = mockDecisionDetails[runId]
  if (!detail) return Promise.reject(new Error(`No decision found for runId "${runId}"`))
  return mockDelay(detail)
}

export function getCompare(_oldId: string, _newId: string): Promise<CompareResult> {
  return mockDelay(mockCompareResult)
}

export function getRegisterDashboard(): Promise<RegisterSummary> {
  return mockDelay(mockRegisterSummary, 400)
}

export function submitPrompt(request: SubmitPromptRequest): Promise<SubmitPromptResponse> {
  const runId = `run-${Date.now()}`
  registerRun(runId, request)
  return mockDelay({ runId }, 200)
}

/** No real run-status machine to mutate in the mock — the abort is already fully handled
 * client-side by the deliberation stream, so this just satisfies the shared contract. */
export function stopDecision(_runId: string): Promise<StopDecisionResponse> {
  return mockDelay({ status: 'stopped' })
}

/**
 * Opens the (mocked) streaming connection for a run started via submitPrompt. Only takes a
 * runId — mirrors a real backend, which already knows the run's prompt/agents from when it was
 * created and wouldn't need them passed again to open its stream.
 */
export function openDeliberationStream(runId: string): DeliberationStreamHandle {
  const config = getRunConfig(runId)
  if (!config) throw new Error(`No run config found for runId "${runId}"`)
  return createMockDeliberationStream(runId, config.prompt, config.agents, config.parentRunId)
}
