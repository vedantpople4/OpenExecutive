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

/** CXOs keep their acronym; specialists get their full name.
 *
 * This used to return initials for everyone, because the label had to fit
 * inside a 2rem circle. Without the pill there is room to be legible, and
 * "Financial Analyst" beats "FA" -- specialist names only appear in team mode,
 * where three of them report to the same CXO and the initials collide. */
function label(name: string): string {
  if (CXO_LABELS[name]) return CXO_LABELS[name]
  return name
    .split('_')
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(' ')
}

export function RoleBadge({ name, role }: RoleBadgeProps) {
  return (
    <span className="role-badge" title={role ?? name}>
      {label(name)}
    </span>
  )
}
