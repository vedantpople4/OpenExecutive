import { useState, type ReactNode } from 'react'
import './CollapsibleSection.css'

interface CollapsibleSectionProps {
  title: ReactNode
  children: ReactNode
  defaultOpen?: boolean
  /** Controlled mode: if provided, overrides internal open state. */
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  open,
  onOpenChange,
}: CollapsibleSectionProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen)
  const isOpen = open ?? internalOpen

  function toggle() {
    const next = !isOpen
    if (onOpenChange) onOpenChange(next)
    else setInternalOpen(next)
  }

  return (
    <div className="collapsible">
      <button
        type="button"
        className="collapsible__trigger"
        onClick={toggle}
        aria-expanded={isOpen}
      >
        <span className={`collapsible__chevron ${isOpen ? 'collapsible__chevron--open' : ''}`}>
          ▸
        </span>
        {title}
      </button>
      {isOpen && <div className="collapsible__body">{children}</div>}
    </div>
  )
}
