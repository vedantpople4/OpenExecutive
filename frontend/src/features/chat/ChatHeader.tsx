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

export function ChatHeader({ parentRunId, hasDecision, tab, onTabChange }: ChatHeaderProps) {
  if (!parentRunId && !hasDecision) return null

  return (
    <div className="chat-header">
      {parentRunId && <BranchChain parentRunId={parentRunId} />}
      {hasDecision && <TabSwitcher tab={tab} onChange={onTabChange} />}
    </div>
  )
}
