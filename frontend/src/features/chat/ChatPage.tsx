import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ChatHeader } from './ChatHeader'
import { ChatPanel } from './ChatPanel'
import { useDeliberationStream } from './hooks/useDeliberationStream'
import { useDecisionDetail } from './hooks/useDecisionDetail'
import { useChatTab } from './hooks/useChatTab'
import { projectEventsToCards } from './projectEventsToCards'
import { projectDecisionDetailToCards } from './projectDecisionDetailToCards'
import { useRunStore } from '../../stores/useRunStore'
import { submitPrompt } from '../../api/endpoints'
import type { BoardDecisionCardData } from './chat.types'
import './ChatPage.css'

/**
 * Handles both `/` (new decision) and `/chat/:runId` (resume/view a run — either the one
 * currently streaming in this session, or a past, persisted decision loaded from history).
 * Owns the submit -> stream -> render wiring and the live-vs-replay branch; ChatPanel and
 * everything below it only receive plain props (a prompt string and a card tree).
 */
export function ChatPage() {
  const { runId: routeRunId } = useParams<{ runId?: string }>()
  const navigate = useNavigate()
  const [tab, setTab] = useChatTab()

  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  // The parent this run was branched from, if any — set at submit time (see handleContinue),
  // distinct from `continuingFrom` below which is the *next* submission's pending parent.
  const [liveRunParentId, setLiveRunParentId] = useState<string | null>(null)
  const [continuingFrom, setContinuingFrom] = useState<{ runId: string; prompt: string } | null>(null)

  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const teamModeEnabled = useRunStore((s) => s.teamModeEnabled)
  const activeRun = useRunStore((s) => s.activeRun)
  const startRun = useRunStore((s) => s.startRun)

  const isViewingActiveRun = activeRun !== null && activeRun.runId === routeRunId
  useDeliberationStream(isViewingActiveRun ? routeRunId! : null)

  // A route pointing at a runId that isn't the in-session active run means the user opened a
  // past, already-persisted decision from history (Sidebar/HistoryItem) — fetch and replay it.
  const isReplayingPastRun = !isViewingActiveRun && routeRunId !== undefined
  const {
    data: decisionDetail,
    isLoading: isDecisionLoading,
    isError: isDecisionError,
  } = useDecisionDetail(isReplayingPastRun ? routeRunId! : null)

  // pendingPrompt/liveRunParentId/continuingFrom are sticky across the submit -> startRun ->
  // navigate sequence so nothing flashes away mid-transition (see plan Section 9). They only
  // clear on an explicit reset (Sidebar's "New Decision", which bumps resetSignal), not on the
  // ordinary null->run transition — so this compares resetSignal during render (React's
  // documented pattern for adjusting state from an external signal) rather than in an effect.
  const resetSignal = useRunStore((s) => s.resetSignal)
  const [seenResetSignal, setSeenResetSignal] = useState(resetSignal)
  if (resetSignal !== seenResetSignal) {
    // React discards this render and immediately retries with the state below already
    // updated, per https://react.dev/reference/react/useState#storing-information-from-previous-renders
    setSeenResetSignal(resetSignal)
    setPendingPrompt(null)
    setLiveRunParentId(null)
    setContinuingFrom(null)
  }

  const cards = useMemo(() => {
    if (isViewingActiveRun && activeRun) return projectEventsToCards(activeRun.events)
    if (isReplayingPastRun && decisionDetail) return projectDecisionDetailToCards(decisionDetail)
    return []
  }, [isViewingActiveRun, activeRun, isReplayingPastRun, decisionDetail])

  const displayPrompt = isReplayingPastRun ? (decisionDetail?.prompt ?? null) : pendingPrompt
  const isLoadingReplay = isReplayingPastRun && isDecisionLoading
  const isErrorReplay = isReplayingPastRun && isDecisionError
  const isStreaming =
    isViewingActiveRun && (activeRun.status === 'connecting' || activeRun.status === 'streaming')
  // Only show a parent breadcrumb when actually viewing a run that has one — not whenever
  // liveRunParentId happens to be non-null from a previous submission in this session (e.g.
  // after navigating back to a fresh "/" without starting a new run).
  const currentParentRunId = isReplayingPastRun
    ? decisionDetail?.parentRunId
    : isViewingActiveRun
      ? liveRunParentId
      : null
  const boardDecisionCard = cards.find(
    (c): c is BoardDecisionCardData => c.kind === 'board_decision',
  )

  async function handleSubmit(prompt: string) {
    setPendingPrompt(prompt)
    setIsSubmitting(true)
    const parentRunId = continuingFrom?.runId
    try {
      const { runId } = await submitPrompt({
        prompt,
        agents: selectedAgents,
        teamModeEnabled,
        parentRunId,
      })
      const controller = new AbortController()
      startRun(runId, controller)
      setLiveRunParentId(parentRunId ?? null)
      setContinuingFrom(null)
      navigate(`/chat/${runId}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleStop() {
    activeRun?.abortController.abort()
  }

  function handleContinueDecision(sourceRunId: string, sourcePrompt: string) {
    setPendingPrompt(null)
    setContinuingFrom({ runId: sourceRunId, prompt: sourcePrompt })
    navigate('/')
  }

  function handleCancelContinue() {
    setContinuingFrom(null)
  }

  return (
    <div className="chat-page">
      <ChatHeader
        parentRunId={currentParentRunId}
        hasDecision={boardDecisionCard !== undefined}
        tab={tab}
        onTabChange={setTab}
      />
      <ChatPanel
        prompt={displayPrompt}
        cards={cards}
        isLoadingReplay={isLoadingReplay}
        isErrorReplay={isErrorReplay}
        isStreaming={isStreaming}
        submitDisabled={isSubmitting || isReplayingPastRun}
        continuingFromPrompt={continuingFrom?.prompt}
        tab={tab}
        boardDecisionCard={boardDecisionCard}
        onSubmit={handleSubmit}
        onStop={handleStop}
        onContinueDecision={handleContinueDecision}
        onCancelContinue={handleCancelContinue}
      />
    </div>
  )
}
