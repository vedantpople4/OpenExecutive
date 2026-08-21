import type { ChatTab } from './hooks/useChatTab'
import './TabSwitcher.css'

interface TabSwitcherProps {
  tab: ChatTab
  onChange: (tab: ChatTab) => void
}

export function TabSwitcher({ tab, onChange }: TabSwitcherProps) {
  return (
    <div className="tab-switcher" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={tab === 'transcript'}
        className={`tab-switcher__tab ${tab === 'transcript' ? 'tab-switcher__tab--active' : ''}`}
        onClick={() => onChange('transcript')}
      >
        Transcript
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={tab === 'summary'}
        className={`tab-switcher__tab ${tab === 'summary' ? 'tab-switcher__tab--active' : ''}`}
        onClick={() => onChange('summary')}
      >
        Decision Summary
      </button>
    </div>
  )
}
