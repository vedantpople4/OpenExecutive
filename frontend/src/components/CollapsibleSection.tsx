import { useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
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
      {/* initial={false} so a section rendered already-open (defaultOpen) does not play an
          expand on first paint -- only a real toggle animates.

          Height lives on the wrapper with overflow hidden, and the padding stays on an inner
          element: padding on the animated element itself never collapses, so a closed section
          would keep a ~12px ghost gap. Deliberately not applied to the PhaseCard/RoundCard
          bodies -- those auto-open when a phase starts running, which is the same moment
          MessageList scrolls to its anchor on cards.length, and an animating height would drag
          that target while the scroll is in flight. This disclosure is user-initiated only. */}
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div className="collapsible__body">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
