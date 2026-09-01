// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MessageList } from './MessageList'
import { projectEventsToCards } from './projectEventsToCards'
import { buildMockTimeline } from '../../api/mock/timeline'

const AGENTS = ['ceo', 'cfo', 'cto', 'cmo'] as const

describe('MessageList', () => {
  it('shows the empty state when there is no active prompt', () => {
    render(<MessageList prompt={null} cards={[]} />)
    expect(screen.getByText('Bring a decision to the board')).toBeInTheDocument()
  })

  it('shows a loading message instead of the empty state while replaying a past decision', () => {
    render(<MessageList prompt={null} cards={[]} isLoadingReplay />)
    expect(screen.getByText('Loading decision...')).toBeInTheDocument()
    expect(screen.queryByText('Bring a decision to the board')).not.toBeInTheDocument()
  })

  it('renders the user prompt bubble and phase cards once a run is in progress', () => {
    const events = buildMockTimeline('run-1', 'Should we hire more engineers?', [...AGENTS])
    const cards = projectEventsToCards(events)
    render(<MessageList prompt="Should we hire more engineers?" cards={cards} />)

    expect(screen.getByText('Should we hire more engineers?')).toBeInTheDocument()
    expect(screen.getByText('Inception')).toBeInTheDocument()
    expect(screen.getByText('Analysis')).toBeInTheDocument()
    expect(screen.getByText('Deliberation')).toBeInTheDocument()
    expect(screen.getByText('Board Decision')).toBeInTheDocument()
  })

  it('shows a speaking indicator for an agent whose report has not landed yet', () => {
    const fullTimeline = buildMockTimeline('run-1', 'test prompt', [...AGENTS])
    const firstSpeakingIndex = fullTimeline.findIndex((e) => e.type === 'agent_speaking')
    const partial = fullTimeline.slice(0, firstSpeakingIndex + 1)
    const cards = projectEventsToCards(partial)

    render(<MessageList prompt="test prompt" cards={cards} />)
    expect(screen.getByText(/is thinking/i)).toBeInTheDocument()
  })
})

describe('MessageList — retrying a failed run', () => {
  const failed = {
    kind: 'error',
    id: 'error-1',
    message: 'LLM provider unreachable after 3 attempts.',
    variant: 'error',
  } as const
  const stopped = {
    kind: 'error',
    id: 'error-2',
    message: 'This deliberation was stopped.',
    variant: 'stopped',
  } as const

  it('re-asks the prompt when the retry button on a failed run is clicked', () => {
    const onRetry = vi.fn()
    render(<MessageList prompt="test prompt" cards={[failed]} onRetry={onRetry} />)

    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('announces a failure to assistive tech but not a stop the user asked for', () => {
    const { rerender } = render(<MessageList prompt="test prompt" cards={[failed]} />)
    expect(screen.getByRole('alert')).toHaveTextContent('LLM provider unreachable')

    rerender(<MessageList prompt="test prompt" cards={[stopped]} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('offers no retry on a stopped run -- the user stopped it on purpose', () => {
    render(<MessageList prompt="test prompt" cards={[stopped]} onRetry={vi.fn()} />)
    expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument()
  })
})
