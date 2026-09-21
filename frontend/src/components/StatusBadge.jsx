export default function StatusBadge({ value }) {
  const normalized = String(value || '').toLowerCase()
  const cls = normalized === 'healthy' || normalized === 'approved' || normalized === 'in' ? 'healthy'
    : normalized === 'low' || normalized === 'sent' || normalized === 'draft' ? 'low'
    : 'out'
  return <span className={`status ${cls}`}>{String(value || '').replaceAll('_',' ')}</span>
}
