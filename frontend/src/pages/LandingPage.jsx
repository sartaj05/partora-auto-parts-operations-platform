import { Link } from 'react-router-dom'

const features = [
  ['01', 'Inventory search', 'Find SKUs, brands, categories and supplier-linked parts in seconds.'],
  ['02', 'Quotation desk', 'Track draft, sent and approved quotes without losing customer context.'],
  ['03', 'Stock signals', 'Surface low and out-of-stock items before they become awkward customer calls.'],
  ['04', 'Supplier control', 'Keep lead times, contacts and sourcing details in one operational view.'],
]

export default function LandingPage() {
  return (
    <div className="landing-shell">
      <header className="site-header container">
        <Link className="brand" to="/"><span className="brand-mark">P</span><span>Partora</span></Link>
        <nav className="site-nav">
          <a href="#workflow">Workflow</a>
          <a href="#trust">Why Partora</a>
          <Link className="text-link" to="/login">Sign in</Link>
          <Link className="button small" to="/login">Open demo</Link>
        </nav>
      </header>

      <main>
        <section className="hero container">
          <div className="hero-copy">
            <span className="eyebrow">Built for parts counters, stores and sales teams</span>
            <h1>Thousands of parts.<br/><span>One calm operating view.</span></h1>
            <p className="hero-lead">Search inventory, prepare quotations, watch stock and coordinate suppliers without forcing your team through spreadsheet archaeology.</p>
            <div className="hero-actions">
              <Link className="button" to="/login">Explore the working demo <span>→</span></Link>
              <a className="button ghost" href="#workflow">See the workflow</a>
            </div>
            <div className="trust-row">
              <span>Fast catalog search</span><span>Role-based access</span><span>Offline demo fallback</span>
            </div>
          </div>

          <div className="hero-panel" aria-label="Partora dashboard preview">
            <div className="panel-top"><span className="dot"></span><span>Operations today</span><span className="live-pill">Live</span></div>
            <div className="metric-grid compact">
              <article><small>Catalog</small><strong>12,840</strong><span>active SKUs</span></article>
              <article><small>Low stock</small><strong>34</strong><span>needs review</span></article>
              <article><small>Quotes</small><strong>18</strong><span>open today</span></article>
              <article><small>Suppliers</small><strong>62</strong><span>approved</span></article>
            </div>
            <div className="preview-table">
              <div className="preview-row header"><span>Part</span><span>Stock</span><span>Status</span></div>
              <div className="preview-row"><span><b>BRK-1048</b><small>Ceramic brake pad</small></span><span>38</span><span className="status healthy">Healthy</span></div>
              <div className="preview-row"><span><b>FLT-2210</b><small>Engine oil filter</small></span><span>8</span><span className="status low">Low</span></div>
              <div className="preview-row"><span><b>RLY-24V4</b><small>24V relay</small></span><span>0</span><span className="status out">Out</span></div>
            </div>
          </div>
        </section>

        <section className="proof-strip">
          <div className="container proof-grid">
            <div><strong>Search-first</strong><span>for busy counters</span></div>
            <div><strong>Clear roles</strong><span>for safer access</span></div>
            <div><strong>Useful signals</strong><span>not dashboard decoration</span></div>
            <div><strong>Demo-ready</strong><span>even without an API</span></div>
          </div>
        </section>

        <section className="section container" id="workflow">
          <div className="section-heading"><span className="eyebrow">Daily workflow</span><h2>From “do we have it?” to a confident quote.</h2><p>Each module is designed around the questions a distributor actually answers all day.</p></div>
          <div className="feature-grid">{features.map(([n,title,body]) => <article className="feature-card" key={n}><span>{n}</span><h3>{title}</h3><p>{body}</p></article>)}</div>
        </section>

        <section className="section container trust-section" id="trust">
          <div className="trust-card">
            <div><span className="eyebrow">Designed for trust</span><h2>Quiet visuals. Strong information hierarchy.</h2></div>
            <p>Partora uses a warm light canvas, ink typography, sage status cues and restrained amber highlights. The goal is to feel dependable at 9:00 AM on a warehouse screen, not like a crypto dashboard escaped into an auto-parts shop.</p>
            <Link className="button" to="/login">Enter demo</Link>
          </div>
        </section>
      </main>
      <footer className="container footer"><div className="brand"><span className="brand-mark">P</span><span>Partora</span></div><span>Auto-parts · Hardware · Electrical operations</span></footer>
    </div>
  )
}
