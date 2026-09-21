import { useState } from 'react'

export default function CreateModal({ title, copy, fields, initial = {}, submitLabel = 'Save', onClose, onSubmit }) {
  const [form, setForm] = useState(initial)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function change(name, value) { setForm(current => ({ ...current, [name]: value })) }
  async function submit(e) {
    e.preventDefault(); setError(''); setSaving(true)
    try { await onSubmit(form); onClose() }
    catch (err) { setError(err.message || 'Could not save') }
    finally { setSaving(false) }
  }

  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
    <form className="create-modal" onSubmit={submit}>
      <div className="modal-head"><div><span className="eyebrow">Quick create</span><h2>{title}</h2><p>{copy}</p></div><button type="button" onClick={onClose}>×</button></div>
      <div className="modal-grid">
        {fields.map(field => <label key={field.name} className={field.span === 2 ? 'span-2' : ''}>{field.label}
          {field.type === 'select' ? <select value={form[field.name] ?? field.default ?? ''} onChange={e => change(field.name,e.target.value)} required={field.required}>
            {(field.options || []).map(opt => <option key={opt.value ?? opt} value={opt.value ?? opt}>{opt.label ?? opt}</option>)}
          </select> : <input type={field.type || 'text'} value={form[field.name] ?? ''} onChange={e => change(field.name,e.target.value)} placeholder={field.placeholder || ''} required={field.required} min={field.min} step={field.step} />}
        </label>)}
      </div>
      {error && <div className="form-error">{error}</div>}
      <div className="modal-actions"><button type="button" className="button ghost" onClick={onClose}>Cancel</button><button className="button" disabled={saving}>{saving ? 'Saving…' : submitLabel}</button></div>
    </form>
  </div>
}
