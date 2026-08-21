import type { DecisionSummary } from '../api/types'

export interface HistoryGroup {
  label: string
  items: DecisionSummary[]
}

const DAY_MS = 24 * 60 * 60 * 1000

/**
 * Buckets an already-recency-sorted decision list into Today/Yesterday/Previous 7 Days/
 * Previous 30 Days/Older-by-month groups. Whether to actually SHOW these group headers (vs.
 * a flat list) is a decision the caller makes, not this function — see plan Section 6.
 */
export function groupHistoryByRecency(
  decisions: DecisionSummary[],
  now: Date = new Date(),
): HistoryGroup[] {
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterdayStart = todayStart - DAY_MS
  const sevenDaysAgo = todayStart - 7 * DAY_MS
  const thirtyDaysAgo = todayStart - 30 * DAY_MS

  const buckets = new Map<string, DecisionSummary[]>()
  const order: string[] = []

  function pushTo(label: string, item: DecisionSummary) {
    if (!buckets.has(label)) {
      buckets.set(label, [])
      order.push(label)
    }
    buckets.get(label)?.push(item)
  }

  for (const decision of decisions) {
    const t = new Date(decision.timestamp).getTime()
    if (t >= todayStart) pushTo('Today', decision)
    else if (t >= yesterdayStart) pushTo('Yesterday', decision)
    else if (t >= sevenDaysAgo) pushTo('Previous 7 Days', decision)
    else if (t >= thirtyDaysAgo) pushTo('Previous 30 Days', decision)
    else {
      const label = new Date(decision.timestamp).toLocaleString('en-US', {
        month: 'long',
        year: 'numeric',
      })
      pushTo(label, decision)
    }
  }

  return order.map((label) => ({ label, items: buckets.get(label) ?? [] }))
}
