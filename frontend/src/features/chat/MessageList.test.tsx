// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
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
