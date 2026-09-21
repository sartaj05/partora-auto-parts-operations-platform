import { useEffect, useState } from 'react'
import { createEndpoint, loadEndpoint } from '../api/client'
import { useAuth } from '../context/AuthContext'
import CreateModal from '../components/CreateModal'

function OpsHeader({ eyebrow, title, copy, action }) {
  return <header className="app-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{copy}</p></div>{action}</header>
}
function Loading(){ return <div className="loading-card">Loading operational data…</div> }
function ErrorBox({ message }){ return <div className="error-card">{message}</div> }
export function BarcodePage(){
  const { user }=useAuth(); const [items,setItems]=useState([]); const [error,setError]=useState(''); const [loading,setLoading]=useState(true); const [creating,setCreating]=useState(false); const [q,setQ]=useState('')
  useEffect(()=>{loadEndpoint('/barcodes/',user.role).then(r=>{setItems(r.data.items);setLoading(false)}).catch(e=>{setError(e.message);setLoading(false)})},[user.role])
  const filtered=items.filter(x=>!q || [x.sku,x.name,x.barcode].join(' ').toLowerCase().includes(q.toLowerCase()))
  async function assign(form){const r=await createEndpoint('/barcodes/',form,user.role);setItems(curr=>[r.item,...curr.filter(x=>x.id!==r.item.id)])}
  return <><OpsHeader eyebrow="Scan desk" title="Barcode & QR labels" copy="Assign, scan and search part labels from one fast inventory surface." action={<button className="button app-action" onClick={()=>setCreating(true)}>Assign label</button>}/>
    <div className="toolbar"><div className="searchbox">▣<input autoFocus placeholder="Scan barcode, QR value or enter SKU…" value={q} onChange={e=>setQ(e.target.value)}/></div><span>{filtered.length} labelled parts</span></div>
    {loading?<Loading/>:error?<ErrorBox message={error}/>:<div className="table-card"><table><thead><tr><th>Part</th><th>Barcode / QR value</th><th>Stock</th><th>Bin</th><th>Label</th></tr></thead><tbody>{filtered.map(x=><tr key={x.id}><td><b>{x.name}</b><small>{x.sku} · {x.brand}</small></td><td><code>{x.barcode || 'Not assigned'}</code></td><td>{x.stock_qty}</td><td>{x.bin_location}</td><td><button className="mini-button" onClick={()=>window.print()}>Print</button></td></tr>)}</tbody></table></div>}
    {creating&&<CreateModal title="Assign barcode" copy="Use an existing barcode/QR value or leave blank to generate an internal Partora code." submitLabel="Assign" onClose={()=>setCreating(false)} onSubmit={assign} fields={[{name:'sku',label:'SKU',required:true},{name:'barcode',label:'Barcode / QR value',placeholder:'8901234567890',span:2}]}/>}</>
}

export function FitmentsPage(){
  const { user }=useAuth(); const [items,setItems]=useState([]); const [q,setQ]=useState(''); const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [creating,setCreating]=useState(false)
  useEffect(()=>{loadEndpoint('/fitments/',user.role).then(r=>{setItems(r.data.items);setLoading(false)}).catch(e=>{setError(e.message);setLoading(false)})},[user.role])
  const filtered=items.filter(x=>!q||[x.make,x.model,x.variant,x.engine,x.oem_number,x.sku,x.product].join(' ').toLowerCase().includes(q.toLowerCase()))
  async function add(form){const r=await createEndpoint('/fitments/',form,user.role);setItems(c=>[r.item,...c])}
  return <><OpsHeader eyebrow="Compatibility" title="Vehicle & part fitment" copy="Find compatible parts by make, model, year, variant, engine or OEM reference." action={<button className="button app-action" onClick={()=>setCreating(true)}>+ Add fitment</button>}/><div className="toolbar"><div className="searchbox">⌕<input placeholder="Swift 2022, i20 1.2L, OEM number…" value={q} onChange={e=>setQ(e.target.value)}/></div><span>{filtered.length} matches</span></div>{loading?<Loading/>:error?<ErrorBox message={error}/>:<div className="table-card"><table><thead><tr><th>Vehicle</th><th>Years</th><th>Variant / Engine</th><th>Part</th><th>OEM</th></tr></thead><tbody>{filtered.map(x=><tr key={x.id}><td><b>{x.make} {x.model}</b></td><td>{x.year_from}–{x.year_to}</td><td>{x.variant}<small>{x.engine}</small></td><td><b>{x.product}</b><small>{x.sku}</small></td><td>{x.oem_number||'—'}</td></tr>)}</tbody></table></div>}{creating&&<CreateModal title="Add vehicle fitment" copy="Map a catalog SKU to vehicle compatibility and OEM references." submitLabel="Add fitment" onClose={()=>setCreating(false)} onSubmit={add} fields={[{name:'sku',label:'SKU',required:true},{name:'make',label:'Make',required:true},{name:'model',label:'Model',required:true},{name:'year_from',label:'From year',type:'number',required:true},{name:'year_to',label:'To year',type:'number'},{name:'variant',label:'Variant'},{name:'engine',label:'Engine'},{name:'oem_number',label:'OEM number'}]}/>}</>
}

export function PurchaseOrdersPage(){
  const { user }=useAuth(); const [items,setItems]=useState([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [creating,setCreating]=useState(false)
  useEffect(()=>{loadEndpoint('/purchase-orders/',user.role).then(r=>{setItems(r.data.items);setLoading(false)}).catch(e=>{setError(e.message);setLoading(false)})},[user.role])
  async function add(form){const r=await createEndpoint('/purchase-orders/',form,user.role);setItems(c=>[r.item,...c])}
  async function receive(id){const r=await createEndpoint('/purchase-orders/',{action:'receive',id},user.role);setItems(c=>c.map(x=>x.id===id?{...x,...r.item}:x))}
  return <><OpsHeader eyebrow="Purchasing" title="Purchase orders" copy="Create supplier orders, track expected delivery and receive stock directly into inventory." action={<button className="button app-action" onClick={()=>setCreating(true)}>+ New PO</button>}/>{loading?<Loading/>:error?<ErrorBox message={error}/>:<div className="table-card"><table><thead><tr><th>PO</th><th>Supplier</th><th>Expected</th><th>Total</th><th>Lines received</th><th>Status</th><th></th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td><b>{x.po_no}</b><small>{x.created_by}</small></td><td>{x.supplier}</td><td>{x.expected_date||'—'}</td><td>₹{Number(x.total||0).toLocaleString('en-IN')}</td><td>{x.received_lines}/{x.line_count}</td><td className="capitalize">{x.status}</td><td>{x.status!=='received'&&<button className="mini-button" onClick={()=>receive(x.id)}>Receive</button>}</td></tr>)}</tbody></table></div>}{creating&&<CreateModal title="New purchase order" copy="Start with one catalog line; additional line-item editing can be layered on this workflow." submitLabel="Create PO" onClose={()=>setCreating(false)} onSubmit={add} initial={{status:'draft',quantity:1}} fields={[{name:'supplier',label:'Supplier',required:true,placeholder:'TorqueLine Components'},{name:'sku',label:'SKU',required:true},{name:'quantity',label:'Quantity',type:'number',required:true,min:'1'},{name:'unit_cost',label:'Unit cost',type:'number',required:true,min:'0',step:'0.01'},{name:'expected_date',label:'Expected date',type:'date'},{name:'status',label:'Status',type:'select',options:['draft','approved','ordered']}]}/>}</>
}
