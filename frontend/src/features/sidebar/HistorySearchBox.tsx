import './HistorySearchBox.css'

interface HistorySearchBoxProps {
  value: string
  onChange: (value: string) => void
}

export function HistorySearchBox({ value, onChange }: HistorySearchBoxProps) {
  return (
    <input
      type="search"
      className="history-search-box"
      aria-label="Search decision history"
      placeholder="Search decisions..."
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}
