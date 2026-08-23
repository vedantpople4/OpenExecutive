import { useInfiniteQuery } from '@tanstack/react-query'
import { getDecisionHistory } from '../../../api/endpoints'

/** q is part of the query key, so a new search term starts a fresh single-page result instead
 * of merging with whatever pages an earlier search had already accumulated. */
export function useDecisionHistory(q: string) {
  const query = useInfiniteQuery({
    queryKey: ['decision-history', q],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      getDecisionHistory({ q: q || undefined, cursor: pageParam, limit: 20 }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
    staleTime: 10_000,
  })

  return {
    decisions: query.data?.pages.flatMap((page) => page.items),
    isLoading: query.isLoading,
    isError: query.isError,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
  }
}
