import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
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

/** Grows the textarea to fit its content, up to a cap, then lets it scroll.
 *
 * Height has to be reset to 'auto' before reading scrollHeight -- otherwise the
 * previous (taller) inline height is still applied and scrollHeight can never
 * report a smaller value, so the box grows but never shrinks back. */
const MAX_TEXTAREA_HEIGHT = 200

function useAutoGrow(value: string) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`
    el.style.overflowY = el.scrollHeight > MAX_TEXTAREA_HEIGHT ? 'auto' : 'hidden'
  }, [value])

  return ref
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

function ArrowUpIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M8 13V3" />
      <path d="M3.5 7.5L8 3l4.5 4.5" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <rect x="4.5" y="4.5" width="7" height="7" rx="1.2" />
    </svg>
  )
}

export function PromptInput({ isStreaming, disabled = false, onSubmit, onStop }: PromptInputProps) {
  const [value, setValue] = useState('')
  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const textareaRef = useAutoGrow(value)
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

  const canSend = !disabled && value.trim() !== '' && selectedAgents.length > 0

  return (
    <form className="prompt-input" onSubmit={handleSubmit}>
      <div className="prompt-input__box">
        <textarea
          ref={textareaRef}
          className="prompt-input__textarea"
          aria-label="Decision prompt"
          placeholder="Bring a decision to the board..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={blocked}
          rows={1}
        />
        {/* One button in one place rather than two that swap position, so the
            control does not move out from under the cursor mid-run. */}
        {isStreaming ? (
          <button
            type="button"
            className="prompt-input__action prompt-input__action--stop"
            onClick={onStop}
            aria-label="Stop the deliberation"
            title="Stop"
          >
            <StopIcon />
          </button>
        ) : (
          <button
            type="submit"
            className="prompt-input__action"
            disabled={!canSend}
            aria-label="Send prompt"
            title="Send"
          >
            <ArrowUpIcon />
          </button>
        )}
      </div>
      <RunConfigSummary />
    </form>
  )
}
