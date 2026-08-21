import { useQuery } from '@tanstack/react-query'
import { getCompare } from '../../../api/endpoints'

export function useCompare(oldId: string | null, newId: string | null) {
  return useQuery({
    queryKey: ['compare', oldId, newId],
    queryFn: () => getCompare(oldId as string, newId as string),
    enabled: oldId !== null && newId !== null,
  })
}
