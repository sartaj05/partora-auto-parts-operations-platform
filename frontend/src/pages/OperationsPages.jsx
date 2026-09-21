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
