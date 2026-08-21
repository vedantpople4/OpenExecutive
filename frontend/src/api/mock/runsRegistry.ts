import type { CXOName } from '../types'

export interface RunConfig {
  prompt: string
  agents: CXOName[]
  teamModeEnabled: boolean
  parentRunId?: string
}

/**
 * Stands in for what a real backend would already know once a run is created via
 * POST /runs (submitPrompt): the streaming endpoint only needs a runId, not the prompt/agents
 * again, because the server already has them. Mirrored here so openDeliberationStream(runId)
 * keeps that same signature against the mock layer.
 */
const registry = new Map<string, RunConfig>()

export function registerRun(runId: string, config: RunConfig): void {
  registry.set(runId, config)
}

export function getRunConfig(runId: string): RunConfig | undefined {
  return registry.get(runId)
}
