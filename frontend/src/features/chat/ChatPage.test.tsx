// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChatPage } from './ChatPage'
import { useRunStore } from '../../stores/useRunStore'
import { registerRun } from '../../api/mock/runsRegistry'

const { stopDecisionMock } = vi.hoisted(() => ({ stopDecisionMock: vi.fn() }))

vi.mock('../../api/endpoints', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api/endpoints')>()
  return { ...actual, stopDecision: stopDecisionMock }
})

function renderChatPageAt(runId: string) {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/chat/${runId}`]}>
        <Routes>
          <Route path="/chat/:runId" element={<ChatPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ChatPage handleStop', () => {
  beforeEach(() => {
    stopDecisionMock.mockReset()
    useRunStore.setState({
      selectedAgents: ['ceo', 'cfo', 'cto', 'cmo'],
      teamModeEnabled: false,
      activeRun: null,
    })
  })

  it('calls stopDecision with the active runId and marks the run stopped', async () => {
    stopDecisionMock.mockResolvedValue({ status: 'stopped' })
    const runId = 'test-run-stop-ok'
    registerRun(runId, { prompt: 'test prompt', agents: ['ceo', 'cfo', 'cto', 'cmo'], teamModeEnabled: false })
    useRunStore.getState().startRun(runId, new AbortController())

    renderChatPageAt(runId)

    fireEvent.click(await screen.findByRole('button', { name: 'Stop' }))

    expect(stopDecisionMock).toHaveBeenCalledTimes(1)
    expect(stopDecisionMock).toHaveBeenCalledWith(runId)
    expect(useRunStore.getState().activeRun?.status).toBe('stopped')
  })

  it('still marks the run stopped locally even if the backend call fails', async () => {
    stopDecisionMock.mockRejectedValue(new Error('network error'))
    const runId = 'test-run-stop-fail'
    registerRun(runId, { prompt: 'test prompt', agents: ['ceo', 'cfo', 'cto', 'cmo'], teamModeEnabled: false })
    useRunStore.getState().startRun(runId, new AbortController())

    renderChatPageAt(runId)

    fireEvent.click(await screen.findByRole('button', { name: 'Stop' }))

    expect(stopDecisionMock).toHaveBeenCalledTimes(1)
    expect(useRunStore.getState().activeRun?.status).toBe('stopped')
  })
})
