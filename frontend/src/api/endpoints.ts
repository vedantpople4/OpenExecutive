/**
 * Single entry point every feature hook imports from. Dispatches to endpoints.mock.ts or
 * endpoints.real.ts based on USE_MOCK_API (client.ts) — both implementations export the exact
 * same function signatures, so nothing above this file needs to know or care which one is live.
 */
import { USE_MOCK_API } from './client'
import * as mockImpl from './endpoints.mock'
import * as realImpl from './endpoints.real'

const impl = USE_MOCK_API ? mockImpl : realImpl

export const getAgents = impl.getAgents
export const getTeamStructure = impl.getTeamStructure
export const getAgentSystemPrompt = impl.getAgentSystemPrompt
export const getDecisionHistory = impl.getDecisionHistory
export const getDecisionDetail = impl.getDecisionDetail
export const getCompare = impl.getCompare
export const getRegisterDashboard = impl.getRegisterDashboard
export const submitPrompt = impl.submitPrompt
export const stopDecision = impl.stopDecision
export const openDeliberationStream = impl.openDeliberationStream

export type {
  SubmitPromptRequest,
  SubmitPromptResponse,
  GetDecisionHistoryParams,
  DecisionHistoryPage,
} from './dto'
