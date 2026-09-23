export default function StatusBadge({ value }) {
  const normalized = String(value || '').toLowerCase()
  const cls = normalized === 'healthy' || normalized === 'approved' || normalized === 'ordered' || normalized === 'received' || normalized === 'fulfilled' || normalized === 'selected' || normalized === 'closed' || normalized === 'in' ? 'healthy'
    : normalized === 'low' || normalized === 'watch' || normalized === 'urgent' || normalized === 'pending' || normalized === 'sent' || normalized === 'quoted' || normalized === 'draft' ? 'low'
    : 'out'
  return <span className={`status ${cls}`}>{String(value || '').replaceAll('_',' ')}</span>
}
