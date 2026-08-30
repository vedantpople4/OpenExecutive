import { BranchChain } from './BranchChain'
import { TabSwitcher } from './TabSwitcher'
import type { ChatTab } from './hooks/useChatTab'
import './ChatHeader.css'

interface ChatHeaderProps {
  parentRunId?: string | null
  hasDecision: boolean
  tab: ChatTab
  onTabChange: (tab: ChatTab) => void
}

/** Run context only. The "OpenExec" title lives in AppShell so it is present
 * on Compare and Dashboard too, not just here. */
export function ChatHeader({ parentRunId, hasDecision, tab, onTabChange }: ChatHeaderProps) {
  if (!parentRunId && !hasDecision) return null

  return (
    <div className="chat-header">
      {parentRunId && <BranchChain parentRunId={parentRunId} />}
      {hasDecision && <TabSwitcher tab={tab} onChange={onTabChange} />}
    </div>
  )
}
