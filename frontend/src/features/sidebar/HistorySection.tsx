import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useDecisionHistory } from './hooks/useDecisionHistory'
import { HistorySearchBox } from './HistorySearchBox'
import { HistoryGroup } from './HistoryGroup'
import { HistoryEmptyState } from './HistoryEmptyState'
import { groupHistoryByRecency } from '../../lib/groupHistoryByRecency'
import './HistorySection.css'

/** Below this count, recency headers add noise rather than structure — render one flat list. */
const GROUPING_MIN_COUNT = 5
const SEARCH_DEBOUNCE_MS = 300

export function HistorySection() {
  const { runId: activeRunId } = useParams<{ runId?: string }>()
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(id)
  }, [search])

  const { decisions, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useDecisionHistory(debouncedSearch)
  const isSearching = debouncedSearch.trim() !== ''

  const groups = useMemo(() => {
    if (!decisions) return []
    const recencyGroups = groupHistoryByRecency(decisions)
    const shouldGroup = decisions.length >= GROUPING_MIN_COUNT && recencyGroups.length > 1
    return shouldGroup ? recencyGroups : [{ label: '', items: decisions }]
  }, [decisions])

  return (
    <section className="sidebar__section sidebar__section--history" aria-label="Decision history">
      <h2 className="sidebar__heading">History</h2>

      {isLoading && <p className="sidebar__placeholder">Loading history...</p>}

      {!isLoading && isError && (
        <p className="sidebar__placeholder" role="alert">
          Couldn't load decision history.
        </p>
      )}

      {!isLoading && !isError && !isSearching && (!decisions || decisions.length === 0) && (
        <HistoryEmptyState />
      )}

      {!isLoading && !isError && (isSearching || (decisions && decisions.length > 0)) && (
        <>
          <HistorySearchBox value={search} onChange={setSearch} />
          {!decisions || decisions.length === 0 ? (
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
          {hasNextPage && (
            // The backend applies search filtering after paging its DynamoDB query, so a click
            // here can occasionally add zero visible items while nextCursor is still non-null —
            // that's expected, not an error; the button just stays available to try again.
            <button
              type="button"
              className="history-section__load-more"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? 'Loading more...' : 'Load more'}
            </button>
          )}
        </>
      )}
    </section>
  )
}
