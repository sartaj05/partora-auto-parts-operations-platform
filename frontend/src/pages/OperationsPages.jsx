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
