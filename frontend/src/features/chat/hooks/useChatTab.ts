import { useSearchParams } from 'react-router-dom'

export type ChatTab = 'transcript' | 'summary'

/** Backs the `/chat/:runId?tab=summary` route (plan Section 1) — tab state lives in the URL,
 * not component state, so it survives refresh/back-forward like any other view of the record. */
export function useChatTab(): [ChatTab, (tab: ChatTab) => void] {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab: ChatTab = searchParams.get('tab') === 'summary' ? 'summary' : 'transcript'

  function setTab(next: ChatTab) {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev)
      if (next === 'transcript') params.delete('tab')
      else params.set('tab', next)
      return params
    })
  }

  return [tab, setTab]
}
