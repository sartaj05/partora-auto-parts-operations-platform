import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { createEndpoint, loadEndpoint } from '../api/client'
import { useAuth } from '../context/AuthContext'
import CreateModal from '../components/CreateModal'
import StatusBadge from '../components/StatusBadge'
import { BarcodePage, VinFitmentPage, MobileWarehousePage, PurchaseOrdersPage, ReceivingPage, WarehouseControlPage, WarehousesPage, ReorderPage, DemandPlanningPage, RFQPage, SalesFlowPage, FulfillmentPage, NotificationsPage, CopilotPage, FinancePage, WarrantyIntelligencePage, ReturnsPage, InventoryControlPage, SupplierIntelligencePage, DealerPortalPage, PortalPage, CustomersPage, PricingPage, CommandCenterPage, GovernancePage, IntegrationsPage, PwaAdminPage, TenancyPage, AutomationPage, FleetPage, SecurityPage, DocumentsPage, DeliveryPage, PartnerApiPage, PredictiveFleetPage, CustomerServicePage, SaasBillingPage, ObservabilityPage, InventoryNetworkPage } from './OperationsPages'

const nav = [
  ['customer_service','/app/customer-service','Customer service','?'],
  ['saas_billing','/app/saas-billing','SaaS billing','$'],
  ['observability','/app/observability','Reliability','~'],
  ['inventory_network','/app/inventory-network','Network planning','<>'],
  ['security','/app/security','Security center','!'],
  ['documents','/app/documents','AI documents','+'],
  ['delivery','/app/delivery','Delivery & POD','>'],
  ['partner_api','/app/partner-api','Partner API','{}'],
  ['predictive_fleet','/app/predictive-fleet','Fleet intelligence','~'],
  ['receiving','/app/receiving','Receiving & matching','+'],
  ['integrations','/app/integrations','Integrations hub','↗'],
  ['pwa_admin','/app/pwa-admin','PWA devices','▣'],
  ['tenancy','/app/tenancy','Organizations','◎'],
  ['automation','/app/automation','Automation','↻'],
  ['fleet','/app/fleet','Fleet service','▤'],
  ['mobile_warehouse','/app/mobile-warehouse','Mobile warehouse','▣'],
  ['notifications','/app/notifications','Notifications','✉'],
  ['copilot','/app/copilot','AI copilot','✦'],
  ['finance','/app/finance','Finance & GST','₹'],
  ['warranty_intelligence','/app/warranty','Warranty insights','↺'],
  ['dashboard','/app','Overview','⌂'],
  ['inventory','/app/inventory','Inventory','⌕'],
  ['quotations','/app/quotations','Quotations','▤'],
  ['suppliers','/app/suppliers','Suppliers','◇'],
  ['stock','/app/stock','Stock','⇅'],
  ['barcodes','/app/barcodes','Barcodes','▣'],
  ['fitments','/app/fitments','Fitments','⌘'],
  ['purchase_orders','/app/purchase-orders','Purchase orders','▥'],
  ['warehouses','/app/warehouses','Warehouses','▦'],
  ['reorder','/app/reorder','Reorder desk','↻'],
  ['demand_planning','/app/demand-planning','Demand planning','✦'],
  ['rfq','/app/rfq','Supplier RFQs','⇄'],
  ['sales_flow','/app/sales-flow','Sales flow','→'],
  ['fulfillment','/app/fulfillment','Fulfillment','✓'],
  ['returns','/app/returns','Returns & RMA','↩'],
  ['inventory_control','/app/inventory-control','Cycle counts','⌗'],
  ['supplier_performance','/app/supplier-performance','Supplier insights','◈'],
  ['portal','/app/portal','Dealer portal','↗'],
  ['crm','/app/customers','Customers','◎'],
  ['pricing','/app/pricing','Pricing','₹'],
  ['analytics','/app/analytics','Analytics','◒'],
  ['governance','/app/governance','Approvals & audit','✓'],
]

function money(n) { return new Intl.NumberFormat('en-IN', { style:'currency', currency:'INR', maximumFractionDigits:0 }).format(n || 0) }
function niceRole(role){ return role ? role[0].toUpperCase()+role.slice(1) : '' }
function dateAfter(days){ const d=new Date(); d.setDate(d.getDate()+days); return d.toISOString().slice(0,10) }

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
  const { user } = useAuth()
  const [query,setQuery]=useState('')
  const [items,setItems]=useState([])
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [creating,setCreating]=useState(false)
  const canCreate=['admin','manager'].includes(user.role)
  useEffect(()=>{ loadEndpoint('/inventory/',user.role).then(r=>{setItems(r.data.items);setLoading(false)}).catch(e=>{setError(e.message);setLoading(false)}) },[user.role])
  const filtered=useMemo(()=>{ const q=query.toLowerCase().trim(); if(!q) return items; return items.filter(i=>[i.sku,i.name,i.brand,i.category,i.supplier].join(' ').toLowerCase().includes(q)) },[items,query])
  async function addItem(form){ const result=await createEndpoint('/inventory/',form,user.role); setItems(current=>[result.item,...current]) }
  return <>
    <PageHeader eyebrow="Catalog" title="Inventory search" copy="Search across SKU, description, brand, category and supplier." action={canCreate?<button className="button app-action" onClick={()=>setCreating(true)}>+ Add item</button>:null} />
    <div className="toolbar"><div className="searchbox">⌕<input placeholder="Search brake pad, MCB-C32, supplier…" value={query} onChange={e=>setQuery(e.target.value)}/></div><span>{filtered.length} items</span></div>
    {loading?<Loading/>:error?<ErrorBox message={error}/>:<div className="table-card"><table><thead><tr><th>Part</th><th>Category</th><th>Supplier</th><th>Location</th><th>Price</th><th>Stock</th><th>Status</th></tr></thead><tbody>{filtered.map(i=><tr key={i.id}><td><b>{i.name}</b><small>{i.sku} · {i.brand}</small></td><td className="capitalize">{i.category}</td><td>{i.supplier}</td><td>{i.bin_location}</td><td>{money(i.price)}</td><td><b>{i.stock_qty}</b><small>Reorder {i.reorder_level}</small></td><td><StatusBadge value={i.stock_status}/></td></tr>)}</tbody></table></div>}
    {creating && <CreateModal title="Add catalog item" copy="Create a searchable SKU with opening stock." submitLabel="Add item" onClose={()=>setCreating(false)} onSubmit={addItem} initial={{category:'auto',stock_qty:0,reorder_level:10}} fields={[
      {name:'sku',label:'SKU',required:true,placeholder:'BRK-2044'}, {name:'name',label:'Part name',required:true,placeholder:'Brake rotor'},
      {name:'brand',label:'Brand',required:true,placeholder:'RoadShield'}, {name:'category',label:'Category',type:'select',options:['auto','hardware','electrical']},
      {name:'supplier',label:'Supplier',placeholder:'TorqueLine Components'}, {name:'bin_location',label:'Bin location',placeholder:'A-03-11'},
      {name:'price',label:'Unit price',type:'number',required:true,min:'0',step:'0.01'}, {name:'stock_qty',label:'Opening stock',type:'number',min:'0'},
      {name:'reorder_level',label:'Reorder level',type:'number',min:'0'}
    ]}/>} 
  </>
}

function Quotations() {
  const { user }=useAuth()
  const [state,setState]=useState({loading:true,items:[],error:''})
  const [creating,setCreating]=useState(false)
  useEffect(()=>{loadEndpoint('/quotations/',user.role).then(r=>setState({loading:false,items:r.data.items,error:''})).catch(e=>setState({loading:false,items:[],error:e.message}))},[user.role])
  async function addQuote(form){ const result=await createEndpoint('/quotations/',form,user.role); setState(current=>({...current,items:[result.item,...current.items]})) }
  return <><PageHeader eyebrow="Sales desk" title="Quotations" copy="Track customer quotes from draft through approval." action={<button className="button app-action" onClick={()=>setCreating(true)}>+ New quotation</button>}/>{state.loading?<Loading/>:state.error?<ErrorBox message={state.error}/>:<div className="table-card"><table><thead><tr><th>Quote</th><th>Customer</th><th>Company</th><th>Total</th><th>Valid until</th><th>Status</th><th>Owner</th></tr></thead><tbody>{state.items.map(q=><tr key={q.id}><td><b>{q.quote_no}</b></td><td>{q.customer_name}</td><td>{q.customer_company}</td><td><b>{money(q.total)}</b></td><td>{q.valid_until}</td><td><StatusBadge value={q.status}/></td><td>{q.created_by}</td></tr>)}</tbody></table></div>}
    {creating && <CreateModal title="New quotation" copy="Create a customer quote for the sales pipeline." submitLabel="Create quote" onClose={()=>setCreating(false)} onSubmit={addQuote} initial={{status:'draft',valid_until:dateAfter(7)}} fields={[
      {name:'customer_name',label:'Customer name',required:true}, {name:'customer_company',label:'Company'},
      {name:'total',label:'Quote total',type:'number',required:true,min:'0',step:'0.01'}, {name:'valid_until',label:'Valid until',type:'date',required:true},
      {name:'status',label:'Status',type:'select',options:['draft','sent','approved'],span:2}
    ]}/>} 
  </>
}

function Suppliers() {
  const { user }=useAuth()
  const [state,setState]=useState({loading:true,items:[],error:''})
  const [creating,setCreating]=useState(false)
  useEffect(()=>{loadEndpoint('/suppliers/',user.role).then(r=>setState({loading:false,items:r.data.items,error:''})).catch(e=>setState({loading:false,items:[],error:e.message}))},[user.role])
  async function addSupplier(form){ const result=await createEndpoint('/suppliers/',form,user.role); setState(current=>({...current,items:[result.item,...current.items]})) }
  return <><PageHeader eyebrow="Sourcing" title="Suppliers" copy="Keep vendor contacts and lead times visible to purchasing teams." action={<button className="button app-action" onClick={()=>setCreating(true)}>+ Add supplier</button>}/>{state.loading?<Loading/>:state.error?<ErrorBox message={state.error}/>:<div className="supplier-grid">{state.items.map(s=><article className="supplier-card" key={s.id}><div className="supplier-icon">{s.name.slice(0,2).toUpperCase()}</div><div><h3>{s.name}</h3><p>{s.contact_name}</p></div><dl><div><dt>Lead time</dt><dd>{s.lead_time_days} days</dd></div><div><dt>Rating</dt><dd>★ {s.rating}</dd></div></dl><small>{s.email}<br/>{s.phone}</small></article>)}</div>}
    {creating && <CreateModal title="Add supplier" copy="Add a vendor contact and normal lead time." submitLabel="Add supplier" onClose={()=>setCreating(false)} onSubmit={addSupplier} initial={{lead_time_days:3,rating:4.0}} fields={[
      {name:'name',label:'Supplier name',required:true,span:2}, {name:'contact_name',label:'Contact person'}, {name:'phone',label:'Phone'},
      {name:'email',label:'Email',type:'email'}, {name:'lead_time_days',label:'Lead time (days)',type:'number',min:'0'},
      {name:'rating',label:'Rating',type:'number',min:'0',step:'0.1'}
    ]}/>} 
  </>
}

function Stock() {
  const { user }=useAuth()
  const [state,setState]=useState({loading:true,items:[],error:''})
  const [creating,setCreating]=useState(false)
  useEffect(()=>{loadEndpoint('/stock/',user.role).then(r=>setState({loading:false,items:r.data.items,error:''})).catch(e=>setState({loading:false,items:[],error:e.message}))},[user.role])
  async function addMovement(form){ const result=await createEndpoint('/stock/',form,user.role); setState(current=>({...current,items:[result.item,...current.items]})) }
  return <><PageHeader eyebrow="Warehouse" title="Stock movements" copy="Recent receipts, issues and adjustments across the store." action={<button className="button app-action" onClick={()=>setCreating(true)}>Record movement</button>}/>{state.loading?<Loading/>:state.error?<ErrorBox message={state.error}/>:<div className="table-card"><table><thead><tr><th>Reference</th><th>Part</th><th>Movement</th><th>Quantity</th><th>Time</th></tr></thead><tbody>{state.items.map(x=><tr key={x.id}><td><b>{x.reference}</b></td><td><b>{x.product}</b><small>{x.sku}</small></td><td><StatusBadge value={x.type}/></td><td>{x.type==='out'?'−':'+'}{x.quantity}</td><td>{new Date(x.created_at).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})}</td></tr>)}</tbody></table></div>}
    {creating && <CreateModal title="Record stock movement" copy="Receive, issue or reset stock for a known SKU." submitLabel="Record movement" onClose={()=>setCreating(false)} onSubmit={addMovement} initial={{type:'in',quantity:1}} fields={[
      {name:'sku',label:'SKU',required:true,placeholder:'BRK-1048'}, {name:'type',label:'Movement',type:'select',options:[{value:'in',label:'Stock in'},{value:'out',label:'Stock out'},{value:'adjustment',label:'Set quantity'}]},
      {name:'quantity',label:'Quantity',type:'number',required:true,min:'1'}, {name:'reference',label:'Reference',placeholder:'GRN-9001'}
    ]}/>} 
  </>
}

function Allowed({ module, children }) { const { modules }=useAuth(); return modules.includes(module)?children:<Navigate to="/app" replace/> }

export default function DashboardPage(){
  return <Shell><Routes>
    <Route index element={<Overview/>}/>
    <Route path="inventory" element={<Allowed module="inventory"><Inventory/></Allowed>}/>
    <Route path="quotations" element={<Allowed module="quotations"><Quotations/></Allowed>}/>
    <Route path="suppliers" element={<Allowed module="suppliers"><Suppliers/></Allowed>}/>
    <Route path="stock" element={<Allowed module="stock"><Stock/></Allowed>}/>
    <Route path="barcodes" element={<Allowed module="barcodes"><BarcodePage/></Allowed>}/>
    <Route path="fitments" element={<Allowed module="fitments"><VinFitmentPage/></Allowed>}/>
    <Route path="purchase-orders" element={<Allowed module="purchase_orders"><PurchaseOrdersPage/></Allowed>}/>
    <Route path="receiving" element={<Allowed module="receiving"><ReceivingPage/></Allowed>}/>
    <Route path="mobile-warehouse" element={<Allowed module="mobile_warehouse"><MobileWarehousePage/></Allowed>}/>
    <Route path="warehouses" element={<Allowed module="warehouses"><WarehouseControlPage/></Allowed>}/>
    <Route path="reorder" element={<Allowed module="reorder"><ReorderPage/></Allowed>}/>
    <Route path="demand-planning" element={<Allowed module="demand_planning"><DemandPlanningPage/></Allowed>}/>
    <Route path="rfq" element={<Allowed module="rfq"><RFQPage/></Allowed>}/>
    <Route path="sales-flow" element={<Allowed module="sales_flow"><SalesFlowPage/></Allowed>}/>
    <Route path="fulfillment" element={<Allowed module="fulfillment"><FulfillmentPage/></Allowed>}/>
    <Route path="notifications" element={<Allowed module="notifications"><NotificationsPage/></Allowed>}/>
    <Route path="copilot" element={<Allowed module="copilot"><CopilotPage/></Allowed>}/>
    <Route path="finance" element={<Allowed module="finance"><FinancePage/></Allowed>}/>
    <Route path="warranty" element={<Allowed module="warranty_intelligence"><WarrantyIntelligencePage/></Allowed>}/>
    <Route path="integrations" element={<Allowed module="integrations"><IntegrationsPage/></Allowed>}/>
    <Route path="pwa-admin" element={<Allowed module="pwa_admin"><PwaAdminPage/></Allowed>}/>
    <Route path="tenancy" element={<Allowed module="tenancy"><TenancyPage/></Allowed>}/>
    <Route path="automation" element={<Allowed module="automation"><AutomationPage/></Allowed>}/>
    <Route path="fleet" element={<Allowed module="fleet"><FleetPage/></Allowed>}/>
    <Route path="security" element={<Allowed module="security"><SecurityPage/></Allowed>}/>
    <Route path="documents" element={<Allowed module="documents"><DocumentsPage/></Allowed>}/>
    <Route path="delivery" element={<Allowed module="delivery"><DeliveryPage/></Allowed>}/>
    <Route path="partner-api" element={<Allowed module="partner_api"><PartnerApiPage/></Allowed>}/>
    <Route path="predictive-fleet" element={<Allowed module="predictive_fleet"><PredictiveFleetPage/></Allowed>}/>
    <Route path="customer-service" element={<Allowed module="customer_service"><CustomerServicePage/></Allowed>}/>
    <Route path="saas-billing" element={<Allowed module="saas_billing"><SaasBillingPage/></Allowed>}/>
    <Route path="observability" element={<Allowed module="observability"><ObservabilityPage/></Allowed>}/>
    <Route path="inventory-network" element={<Allowed module="inventory_network"><InventoryNetworkPage/></Allowed>}/>
    <Route path="returns" element={<Allowed module="returns"><ReturnsPage/></Allowed>}/>
    <Route path="inventory-control" element={<Allowed module="inventory_control"><InventoryControlPage/></Allowed>}/>
    <Route path="supplier-performance" element={<Allowed module="supplier_performance"><SupplierIntelligencePage/></Allowed>}/>
    <Route path="portal" element={<Allowed module="portal"><DealerPortalPage/></Allowed>}/>
    <Route path="customers" element={<Allowed module="crm"><CustomersPage/></Allowed>}/>
    <Route path="pricing" element={<Allowed module="pricing"><PricingPage/></Allowed>}/>
    <Route path="analytics" element={<Allowed module="analytics"><CommandCenterPage/></Allowed>}/>
    <Route path="governance" element={<Allowed module="governance"><GovernancePage/></Allowed>}/>
    <Route path="*" element={<Navigate to="/app" replace/>}/>
  </Routes></Shell>
}
