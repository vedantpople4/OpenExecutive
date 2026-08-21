import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useDecisionHistory } from './hooks/useDecisionHistory'
import { HistorySearchBox } from './HistorySearchBox'
import { HistoryGroup } from './HistoryGroup'
import { HistoryEmptyState } from './HistoryEmptyState'
import { groupHistoryByRecency } from '../../lib/groupHistoryByRecency'

/** Below this count, recency headers add noise rather than structure — render one flat list. */
const GROUPING_MIN_COUNT = 5

export function HistorySection() {
  const { runId: activeRunId } = useParams<{ runId?: string }>()
  const [search, setSearch] = useState('')
  const { data: decisions, isLoading, isError } = useDecisionHistory()

  const filtered = useMemo(() => {
    if (!decisions) return []
    const query = search.trim().toLowerCase()
    if (!query) return decisions
    return decisions.filter((d) => d.prompt.toLowerCase().includes(query))
  }, [decisions, search])

  const groups = useMemo(() => {
    const recencyGroups = groupHistoryByRecency(filtered)
    const shouldGroup = filtered.length >= GROUPING_MIN_COUNT && recencyGroups.length > 1
    return shouldGroup ? recencyGroups : [{ label: '', items: filtered }]
  }, [filtered])

  return (
    <section className="sidebar__section sidebar__section--history" aria-label="Decision history">
      <h2 className="sidebar__heading">History</h2>

      {isLoading && <p className="sidebar__placeholder">Loading history...</p>}

      {!isLoading && isError && (
        <p className="sidebar__placeholder" role="alert">
          Couldn't load decision history.
        </p>
      )}

      {!isLoading && !isError && (!decisions || decisions.length === 0) && <HistoryEmptyState />}

      {!isLoading && !isError && decisions && decisions.length > 0 && (
        <>
          <HistorySearchBox value={search} onChange={setSearch} />
          {filtered.length === 0 ? (
            <p className="sidebar__placeholder">No matches.</p>
          ) : (
            <div className="history-section__groups">
              {groups.map((group, i) => (
                <HistoryGroup
                  key={group.label || i}
                  label={group.label}
                  items={group.items}
                  activeRunId={activeRunId}
                />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
