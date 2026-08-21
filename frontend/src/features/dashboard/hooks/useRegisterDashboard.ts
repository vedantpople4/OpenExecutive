import { useQuery } from '@tanstack/react-query'
import { getRegisterDashboard } from '../../../api/endpoints'

export function useRegisterDashboard() {
  return useQuery({ queryKey: ['register-dashboard'], queryFn: getRegisterDashboard })
}
