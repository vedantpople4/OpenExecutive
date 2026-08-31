import type { Agent, DecisionDetail, TeamStructure } from './types'
import type {
  SubmitPromptRequest,
  SubmitPromptResponse,
  StopDecisionResponse,
  GetDecisionHistoryParams,
  DecisionHistoryPage,
  DeliberationStreamHandle,
} from './dto'
import { API_BASE_URL } from './client'
import type { CompareResult, RegisterSummary } from './types'

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export function getAgents(): Promise<Agent[]> {
  return apiFetch<Agent[]>('/agents')
}

export function getTeamStructure(): Promise<TeamStructure> {
  return apiFetch<TeamStructure>('/teams')
}

export async function getAgentSystemPrompt(agentName: string): Promise<string> {
  const { prompt } = await apiFetch<{ prompt: string }>(`/agents/${encodeURIComponent(agentName)}/prompt`)
  return prompt
}

export function getDecisionHistory(params: GetDecisionHistoryParams = {}): Promise<DecisionHistoryPage> {
  const search = new URLSearchParams()
  if (params.q) search.set('q', params.q)
  if (params.cursor) search.set('cursor', params.cursor)
  if (params.limit !== undefined) search.set('limit', String(params.limit))
  const qs = search.toString()
  return apiFetch<DecisionHistoryPage>(`/decisions${qs ? `?${qs}` : ''}`)
}

export function getDecisionDetail(runId: string): Promise<DecisionDetail> {
  return apiFetch<DecisionDetail>(`/decisions/${encodeURIComponent(runId)}`)
}

export function getCompare(oldId: string, newId: string): Promise<CompareResult> {
  const params = new URLSearchParams({ old: oldId, new: newId })
  return apiFetch<CompareResult>(`/compare?${params.toString()}`)
}

export function getRegisterDashboard(): Promise<RegisterSummary> {
  return apiFetch<RegisterSummary>('/dashboard')
}

export function submitPrompt(request: SubmitPromptRequest): Promise<SubmitPromptResponse> {
  return apiFetch<SubmitPromptResponse>('/decisions', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export function stopDecision(runId: string): Promise<StopDecisionResponse> {
  return apiFetch<StopDecisionResponse>(`/decisions/${encodeURIComponent(runId)}/stop`, {
    method: 'POST',
  })
}

/** 204 No Content, so there is no body to parse -- apiFetch would choke on
 * response.json(). Rejects with the server's message on 409 (still running)
 * and 404 so the caller can surface why nothing was deleted. */
export async function deleteDecision(runId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/decisions/${encodeURIComponent(runId)}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const detail = await response
      .json()
      .then((body: { detail?: string }) => body.detail)
      .catch(() => undefined)
    throw new Error(detail ?? `Could not delete this decision (${response.status})`)
  }
}

/**
 * A real EventSource already satisfies DeliberationStreamHandle structurally — this just adapts
 * its addEventListener's Event-typed listener to the narrower {data: string}/{message: string}
 * shape the hook expects (they're structurally compatible; MessageEvent has .data, ErrorEvent
 * reporting here just needs .message).
 */
export function openDeliberationStream(runId: string): DeliberationStreamHandle {
  const source = new EventSource(`${API_BASE_URL}/decisions/${encodeURIComponent(runId)}/events`)
  const handle: DeliberationStreamHandle = {
    addEventListener(type, listener) {
      source.addEventListener(type, listener as unknown as EventListener)
    },
    close() {
      source.close()
    },
  }
  return handle
}
