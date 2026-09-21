import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { loadEndpoint } from '../api/client'
import { useAuth } from '../context/AuthContext'
import StatusBadge from '../components/StatusBadge'

const nav = [
  ['dashboard','/app','Overview','⌂'],
  ['inventory','/app/inventory','Inventory','⌕'],
  ['quotations','/app/quotations','Quotations','▤'],
  ['suppliers','/app/suppliers','Suppliers','◇'],
  ['stock','/app/stock','Stock','⇅'],
]

function money(n) { return new Intl.NumberFormat('en-IN', { style:'currency', currency:'INR', maximumFractionDigits:0 }).format(n || 0) }
function niceRole(role){ return role ? role[0].toUpperCase()+role.slice(1) : '' }

function Shell({ children }) {
  const { user, modules, demoMode, logout } = useAuth()
  const location = useLocation()
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand app-brand" to="/"><span className="brand-mark">P</span><span>Partora</span></Link>
        <div className="workspace-tag">Operations workspace</div>
        <nav className="app-nav">
          {nav.filter(([key]) => modules.includes(key)).map(([key,path,label,icon]) => {
            const active = path === '/app' ? location.pathname === '/app' : location.pathname.startsWith(path)
            return <Link className={active ? 'active' : ''} key={key} to={path}><span>{icon}</span>{label}</Link>
          })}
        </nav>
        <div className="sidebar-foot">
          {demoMode && <div className="demo-mode"><span></span><div><b>Demo mode</b><small>Using local fallback data</small></div></div>}
          <div className="user-chip"><div className="avatar">{user.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><div><b>{user.name}</b><small>{niceRole(user.role)}</small></div><button onClick={logout} title="Sign out">↗</button></div>
        </div>
      </aside>
      <main className="app-main">{children}</main>
    </div>
  )
}

function PageHeader({ eyebrow, title, copy, action }) {
  return <header className="app-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{copy}</p></div>{action}</header>
}

function Loading(){ return <div className="loading-card">Loading operational data…</div> }
function ErrorBox({ message }){ return <div className="error-card">{message}</div> }

function Overview() {
  const { user } = useAuth()
  const [state,setState] = useState({loading:true,data:null,error:''})
  useEffect(()=>{ loadEndpoint('/dashboard/',user.role).then(r=>setState({loading:false,data:r.data,error:''})).catch(e=>setState({loading:false,data:null,error:e.message})) },[user.role])
  if(state.loading) return <Loading/>
  if(state.error) return <ErrorBox message={state.error}/>
  const d=state.data
  return <>
    <PageHeader eyebrow="Today" title={`Good afternoon, ${user.name.split(' ')[0]}.`} copy="Here is the operational picture across catalog, quotes and replenishment." action={<Link className="button app-action" to="/app/inventory">Search inventory</Link>} />
    <section className="metric-grid dashboard-metrics">
      <article><small>Catalog items</small><strong>{d.metrics.products}</strong><span>searchable SKUs</span></article>
      <article><small>Stock attention</small><strong>{d.metrics.low_stock}</strong><span>low or unavailable</span></article>
      <article><small>Open quotations</small><strong>{d.metrics.open_quotes}</strong><span>draft or sent</span></article>
      <article><small>Active suppliers</small><strong>{d.metrics.suppliers}</strong><span>approved vendors</span></article>
    </section>
    <section className="dashboard-grid">
      <article className="data-card">
        <div className="card-title"><div><span className="eyebrow">Attention</span><h2>Stock watchlist</h2></div><Link to="/app/inventory">View inventory →</Link></div>
        <div className="simple-list">{d.low_stock_items.map(item=><div className="simple-row" key={item.sku}><div><b>{item.name}</b><small>{item.sku} · {item.bin_location}</small></div><strong>{item.stock_qty}</strong><StatusBadge value={item.stock_status}/></div>)}</div>
      </article>
      <article className="data-card">
        <div className="card-title"><div><span className="eyebrow">Sales</span><h2>Recent quotations</h2></div></div>
        <div className="simple-list">{d.recent_quotes.map(q=><div className="quote-row" key={q.quote_no}><div><b>{q.customer_company || q.customer_name}</b><small>{q.quote_no} · {q.customer_name}</small></div><strong>{money(q.total)}</strong><StatusBadge value={q.status}/></div>)}</div>
      </article>
    </section>
  </>
}

function Inventory() {
  const { user } = useAuth(); const [query,setQuery]=useState(''); const [items,setItems]=useState([]); const [loading,setLoading]=useState(true); const [error,setError]=useState('')
  useEffect(()=>{ loadEndpoint('/inventory/',user.role).then(r=>{setItems(r.data.items);setLoading(false)}).catch(e=>{setError(e.message);setLoading(false)}) },[user.role])
  const filtered=useMemo(()=>{ const q=query.toLowerCase().trim(); if(!q) return items; return items.filter(i=>[i.sku,i.name,i.brand,i.category,i.supplier].join(' ').toLowerCase().includes(q)) },[items,query])
  return <>
    <PageHeader eyebrow="Catalog" title="Inventory search" copy="Search across SKU, description, brand, category and supplier." action={<button className="button app-action">+ Add item</button>} />
    <div className="toolbar"><div className="searchbox">⌕<input placeholder="Search brake pad, MCB-C32, supplier…" value={query} onChange={e=>setQuery(e.target.value)}/></div><span>{filtered.length} items</span></div>
    {loading?<Loading/>:error?<ErrorBox message={error}/>:<div className="table-card"><table><thead><tr><th>Part</th><th>Category</th><th>Supplier</th><th>Location</th><th>Price</th><th>Stock</th><th>Status</th></tr></thead><tbody>{filtered.map(i=><tr key={i.id}><td><b>{i.name}</b><small>{i.sku} · {i.brand}</small></td><td className="capitalize">{i.category}</td><td>{i.supplier}</td><td>{i.bin_location}</td><td>{money(i.price)}</td><td><b>{i.stock_qty}</b><small>Reorder {i.reorder_level}</small></td><td><StatusBadge value={i.stock_status}/></td></tr>)}</tbody></table></div>}
  </>
}

function Quotations() {
  const { user }=useAuth(); const [state,setState]=useState({loading:true,items:[],error:''})
  useEffect(()=>{loadEndpoint('/quotations/',user.role).then(r=>setState({loading:false,items:r.data.items,error:''})).catch(e=>setState({loading:false,items:[],error:e.message}))},[user.role])
  return <><PageHeader eyebrow="Sales desk" title="Quotations" copy="Track customer quotes from draft through approval." action={<button className="button app-action">+ New quotation</button>}/>{state.loading?<Loading/>:state.error?<ErrorBox message={state.error}/>:<div className="table-card"><table><thead><tr><th>Quote</th><th>Customer</th><th>Company</th><th>Total</th><th>Valid until</th><th>Status</th><th>Owner</th></tr></thead><tbody>{state.items.map(q=><tr key={q.id}><td><b>{q.quote_no}</b></td><td>{q.customer_name}</td><td>{q.customer_company}</td><td><b>{money(q.total)}</b></td><td>{q.valid_until}</td><td><StatusBadge value={q.status}/></td><td>{q.created_by}</td></tr>)}</tbody></table></div>}</>
}

function Suppliers() {
  const { user }=useAuth(); const [state,setState]=useState({loading:true,items:[],error:''})
  useEffect(()=>{loadEndpoint('/suppliers/',user.role).then(r=>setState({loading:false,items:r.data.items,error:''})).catch(e=>setState({loading:false,items:[],error:e.message}))},[user.role])
  return <><PageHeader eyebrow="Sourcing" title="Suppliers" copy="Keep vendor contacts and lead times visible to purchasing teams." action={<button className="button app-action">+ Add supplier</button>}/>{state.loading?<Loading/>:state.error?<ErrorBox message={state.error}/>:<div className="supplier-grid">{state.items.map(s=><article className="supplier-card" key={s.id}><div className="supplier-icon">{s.name.slice(0,2).toUpperCase()}</div><div><h3>{s.name}</h3><p>{s.contact_name}</p></div><dl><div><dt>Lead time</dt><dd>{s.lead_time_days} days</dd></div><div><dt>Rating</dt><dd>★ {s.rating}</dd></div></dl><small>{s.email}<br/>{s.phone}</small></article>)}</div>}</>
}

function Stock() {
  const { user }=useAuth(); const [state,setState]=useState({loading:true,items:[],error:''})
  useEffect(()=>{loadEndpoint('/stock/',user.role).then(r=>setState({loading:false,items:r.data.items,error:''})).catch(e=>setState({loading:false,items:[],error:e.message}))},[user.role])
  return <><PageHeader eyebrow="Warehouse" title="Stock movements" copy="Recent receipts, issues and adjustments across the store." action={<button className="button app-action">Record movement</button>}/>{state.loading?<Loading/>:state.error?<ErrorBox message={state.error}/>:<div className="table-card"><table><thead><tr><th>Reference</th><th>Part</th><th>Movement</th><th>Quantity</th><th>Time</th></tr></thead><tbody>{state.items.map(x=><tr key={x.id}><td><b>{x.reference}</b></td><td><b>{x.product}</b><small>{x.sku}</small></td><td><StatusBadge value={x.type}/></td><td>{x.type==='out'?'−':'+'}{x.quantity}</td><td>{new Date(x.created_at).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}</td></tr>)}</tbody></table></div>}</>
}

function Allowed({ module, children }) { const { modules }=useAuth(); return modules.includes(module)?children:<Navigate to="/app" replace/> }

export default function DashboardPage(){
  return <Shell><Routes>
    <Route index element={<Overview/>}/>
    <Route path="inventory" element={<Allowed module="inventory"><Inventory/></Allowed>}/>
    <Route path="quotations" element={<Allowed module="quotations"><Quotations/></Allowed>}/>
    <Route path="suppliers" element={<Allowed module="suppliers"><Suppliers/></Allowed>}/>
    <Route path="stock" element={<Allowed module="stock"><Stock/></Allowed>}/>
    <Route path="*" element={<Navigate to="/app" replace/>}/>
  </Routes></Shell>
}
