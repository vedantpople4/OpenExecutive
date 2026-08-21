import './UserPromptBubble.css'

interface UserPromptBubbleProps {
  prompt: string
}

/**
 * Renders from local optimistic state the instant PromptInput submits, before the submit
 * mutation resolves — matching how ChatGPT/Claude show your own message instantly rather than
 * waiting on a round trip (see plan Section 9).
 */
export function UserPromptBubble({ prompt }: UserPromptBubbleProps) {
  return (
    <div className="user-prompt-bubble">
      <p>{prompt}</p>
    </div>
  )
}
