import { useState } from 'react'
import { useAgentSystemPrompt } from './hooks/useAgentSystemPrompt'
import './AgentPromptPreview.css'

interface AgentPromptPreviewProps {
  agentName: string
}

const PREVIEW_LINE_COUNT = 3

export function AgentPromptPreview({ agentName }: AgentPromptPreviewProps) {
  const [expanded, setExpanded] = useState(false)
  const { data: prompt, isLoading, isError } = useAgentSystemPrompt(agentName)

  if (isError) {
    return (
      <p className="agent-prompt-preview__loading" role="alert">
        Couldn't load this agent's prompt.
      </p>
    )
  }

  if (isLoading || !prompt) {
    return <p className="agent-prompt-preview__loading">Loading prompt...</p>
  }

  const lines = prompt.trim().split('\n')
  const isTruncatable = lines.length > PREVIEW_LINE_COUNT
  const visibleText = expanded ? lines.join('\n') : lines.slice(0, PREVIEW_LINE_COUNT).join('\n')

  return (
    <div className="agent-prompt-preview">
      <pre className="agent-prompt-preview__text">{visibleText}</pre>
      {isTruncatable && (
        <button type="button" className="agent-prompt-preview__toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Show less' : 'Show full prompt'}
        </button>
      )}
    </div>
  )
}
