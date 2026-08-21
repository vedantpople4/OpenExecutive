import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { useRunStore } from '../../stores/useRunStore'
import './PromptInput.css'

interface PromptInputProps {
  /** True once a run is actually streaming and can be aborted — shows Stop instead of Send. */
  isStreaming: boolean
  /** True while submission is blocked for any other reason (in-flight submit, no agents selected). */
  disabled?: boolean
  onSubmit: (prompt: string) => void
  onStop: () => void
}

function RunConfigSummary() {
  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const teamModeEnabled = useRunStore((s) => s.teamModeEnabled)

  return (
    <p className="prompt-input__config-summary">
      {selectedAgents.length === 0
        ? 'No agents selected'
        : selectedAgents.map((a) => a.toUpperCase()).join(', ')}
      {teamModeEnabled && ' · specialist teams enabled'}
    </p>
  )
}

export function PromptInput({ isStreaming, disabled = false, onSubmit, onStop }: PromptInputProps) {
  const [value, setValue] = useState('')
  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const blocked = isStreaming || disabled

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || blocked || selectedAgents.length === 0) return
    onSubmit(trimmed)
    setValue('')
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    submit()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <form className="prompt-input" onSubmit={handleSubmit}>
      <RunConfigSummary />
      <div className="prompt-input__row">
        <textarea
          className="prompt-input__textarea"
          aria-label="Decision prompt"
          placeholder="Bring a decision to the board..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={blocked}
          rows={2}
        />
        {isStreaming ? (
          <button type="button" className="prompt-input__stop" onClick={onStop}>
            Stop
          </button>
        ) : (
          <button
            type="submit"
            className="prompt-input__submit"
            disabled={disabled || !value.trim() || selectedAgents.length === 0}
          >
            Send
          </button>
        )}
      </div>
    </form>
  )
}
