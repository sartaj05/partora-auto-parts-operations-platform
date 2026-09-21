import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { demoAccounts } from '../mock/data'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@partora.demo')
  const [password, setPassword] = useState('demo123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to="/app" replace />

  async function submit(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try { await login(email, password); navigate('/app') }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  function useAccount(account) { setEmail(account.email); setPassword(account.password); setError('') }

  return (
    <div className="login-layout">
      <section className="login-aside">
        <Link className="brand inverse" to="/"><span className="brand-mark light">P</span><span>Partora</span></Link>
        <div className="login-aside-copy">
          <span className="eyebrow pale">Operations workspace</span>
          <h1>Know the stock.<br/>Quote with confidence.</h1>
          <p>One calm view for fast-moving parts counters, warehouse teams and managers.</p>
        </div>
        <div className="aside-note"><span>✓</span><p><b>Demo-safe by design</b><br/>If Django is offline, the React app automatically uses local demo data.</p></div>
      </section>
      <main className="login-main">
        <div className="login-card">
          <Link className="back-link" to="/">← Back to site</Link>
          <span className="eyebrow">Secure access</span>
          <h2>Welcome back</h2>
          <p className="muted">Sign in with a team account or pick a demo role below.</p>
          <form onSubmit={submit}>
            <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" required /></label>
            <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
            {error && <div className="form-error">{error}</div>}
            <button className="button login-button" disabled={loading}>{loading ? 'Checking…' : 'Sign in to workspace'}<span>→</span></button>
          </form>
          <div className="demo-divider"><span>Demo roles</span></div>
          <div className="demo-accounts">
            {demoAccounts.map(a => <button key={a.role} type="button" onClick={() => useAccount(a)}><b>{a.role}</b><span>{a.email}</span></button>)}
          </div>
          <p className="login-footnote">All demo accounts use <code>demo123</code>. Revolutionary security, strictly for the demo universe.</p>
        </div>
      </main>
    </div>
  )
}
