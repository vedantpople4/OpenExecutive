// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChatPage } from './ChatPage'
import { useRunStore } from '../../stores/useRunStore'
import { registerRun } from '../../api/mock/runsRegistry'

const { stopDecisionMock, submitPromptMock } = vi.hoisted(() => ({
  stopDecisionMock: vi.fn(),
  submitPromptMock: vi.fn(),
}))

vi.mock('../../api/endpoints', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../api/endpoints')>()
  return { ...actual, stopDecision: stopDecisionMock, submitPrompt: submitPromptMock }
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

    fireEvent.click(await screen.findByRole('button', { name: 'Stop the deliberation' }))

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

    fireEvent.click(await screen.findByRole('button', { name: 'Stop the deliberation' }))

    expect(stopDecisionMock).toHaveBeenCalledTimes(1)
    expect(useRunStore.getState().activeRun?.status).toBe('stopped')
  })
})

describe('ChatPage — a submit that never reaches the server', () => {
  beforeEach(() => {
    submitPromptMock.mockReset()
    useRunStore.setState({
      selectedAgents: ['ceo', 'cfo', 'cto', 'cmo'],
      teamModeEnabled: false,
      activeRun: null,
    })
  })

  function renderNewDecisionPage() {
    const queryClient = new QueryClient()
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<ChatPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  async function submit(prompt: string) {
    fireEvent.change(await screen.findByRole('textbox', { name: /decision prompt/i }), {
      target: { value: prompt },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send prompt' }))
  }

  it('surfaces the failure instead of leaving the prompt bubble hanging', async () => {
    submitPromptMock.mockRejectedValue(new Error('Failed to fetch'))
    renderNewDecisionPage()

    await submit('will not reach the server')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      "Couldn't start this deliberation: Failed to fetch",
    )
  })

  it('lets the user retry, and clears the failure once the retry gets through', async () => {
    submitPromptMock.mockRejectedValueOnce(new Error('Failed to fetch'))
    renderNewDecisionPage()

    await submit('will not reach the server')
    await screen.findByRole('alert')

    submitPromptMock.mockResolvedValueOnce({ runId: 'run-after-retry' })
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

    await vi.waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
    expect(submitPromptMock).toHaveBeenCalledTimes(2)
  })
})
