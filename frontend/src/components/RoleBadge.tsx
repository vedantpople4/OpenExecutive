import './RoleBadge.css'

interface RoleBadgeProps {
  name: string // e.g. "ceo" or a specialist name like "financial_analyst"
  role?: string // e.g. "Chief Executive Officer"
}

const CXO_LABELS: Record<string, string> = {
  ceo: 'CEO',
  cfo: 'CFO',
  cto: 'CTO',
  cmo: 'CMO',
}

function initials(name: string): string {
  if (CXO_LABELS[name]) return CXO_LABELS[name]
  return name
    .split('_')
    .map((part) => part[0]?.toUpperCase())
    .join('')
    .slice(0, 3)
}

export function RoleBadge({ name, role }: RoleBadgeProps) {
  return (
    <span className={`role-badge role-badge--${name}`} title={role ?? name}>
      {initials(name)}
    </span>
  )
}
