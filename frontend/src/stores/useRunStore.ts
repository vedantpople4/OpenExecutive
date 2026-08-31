import { create } from 'zustand'
import type { CXOName, DeliberationEvent } from '../api/types'

export type RunStatus = 'idle' | 'connecting' | 'streaming' | 'complete' | 'stopped' | 'error'

export interface ActiveRun {
  runId: string
  status: RunStatus
  events: DeliberationEvent[]
  abortController: AbortController
}

interface RunStoreState {
  selectedAgents: CXOName[]
  teamModeEnabled: boolean
  activeRun: ActiveRun | null
  /** Increments on every explicit resetActiveRun() call, so consumers can distinguish an
   * intentional reset (e.g. "New Decision") from the ordinary null->run transition. */
  resetSignal: number

  setSelectedAgents: (agents: CXOName[]) => void
  toggleAgent: (agent: CXOName) => void
  toggleTeamMode: () => void
  startRun: (runId: string, abortController: AbortController) => void
  appendEvent: (event: DeliberationEvent) => void
  setRunStatus: (status: RunStatus) => void
  resetActiveRun: () => void
}

const DEFAULT_AGENTS: CXOName[] = ['ceo', 'cfo', 'cto', 'cmo']

export const useRunStore = create<RunStoreState>((set) => ({
  selectedAgents: DEFAULT_AGENTS,
  teamModeEnabled: false,
  activeRun: null,
  resetSignal: 0,

  setSelectedAgents: (agents) => set({ selectedAgents: agents }),

  toggleAgent: (agent) =>
    set((state) => ({
      selectedAgents: state.selectedAgents.includes(agent)
        ? state.selectedAgents.filter((a) => a !== agent)
        : DEFAULT_AGENTS.filter((a) => state.selectedAgents.includes(a) || a === agent),
    })),

  toggleTeamMode: () => set((state) => ({ teamModeEnabled: !state.teamModeEnabled })),

  startRun: (runId, abortController) =>
    set({
      activeRun: { runId, status: 'connecting', events: [], abortController },
    }),

  appendEvent: (event) =>
    set((state) => {
      if (!state.activeRun) return state
      // EventSource reconnects on its own after a transient network error, and the backend
      // replays the whole stored history from the top on every connect (no Last-Event-ID
      // handling in backend/app/routers/events.py). Without this guard a single reconnect
      // leaves every event in the log twice, which the projectors then fold into duplicate
      // report/round/decision cards sharing one id.
      //
      // event_id is the identity: to_wire_event() defaults it to '' when absent, so an
      // id-less event is passed through rather than collapsing all of them into one.
      if (event.event_id && state.activeRun.events.some((e) => e.event_id === event.event_id)) {
        return state
      }
      return {
        activeRun: {
          ...state.activeRun,
          events: [...state.activeRun.events, event],
        },
      }
    }),

  setRunStatus: (status) =>
    set((state) => {
      if (!state.activeRun) return state
      return { activeRun: { ...state.activeRun, status } }
    }),

  resetActiveRun: () => set((state) => ({ activeRun: null, resetSignal: state.resetSignal + 1 })),
}))
