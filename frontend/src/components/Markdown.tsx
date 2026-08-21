import ReactMarkdown from 'react-markdown'
import './Markdown.css'

interface MarkdownProps {
  children: string
}

/** Shared renderer for long-form agent text fields (summaries, reasoning, etc.). */
export function Markdown({ children }: MarkdownProps) {
  return (
    <div className="markdown">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  )
}
