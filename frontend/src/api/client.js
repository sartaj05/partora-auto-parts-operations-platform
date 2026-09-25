import { analyticsData, automationState, billingState, copilotState, customerServiceState, customers, deliveryState, demandPlanningData, demandPlanningState, demoAccounts, documentState, financeState, fitments, fleetState, fulfillmentState, governanceState, integrationsState, inventory, inventoryControlState, inventoryNetworkState, mockDashboard, mobileWarehouseState, modulesByRole, notificationState, observabilityState, partnerApiState, portalState, predictiveFleetState, priceRules, pwaState, purchaseOrders, quotations, receivingState, reorderSuggestions, returnsState, rfqState, salesFlow, securityState, stock, supplierPerformanceState, suppliers, tenantState, vinVehicles, warehouseState, warrantyState } from '../mock/data'

const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const NETWORK_MESSAGE = 'Backend unavailable. Demo mode is active.'

function sleep(ms = 180) { return new Promise(resolve => setTimeout(resolve, ms)) }

function getStoredToken() { return localStorage.getItem('partora_token') }

async function request(path, options = {}) {
  const token = getStoredToken()
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(localStorage.getItem('partora_branch') ? { 'X-Partora-Branch': localStorage.getItem('partora_branch') } : {}),
      ...(options.headers || {}),
    },
  })
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) throw new Error('API is not connected')
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw Object.assign(new Error(body.detail || 'Request failed'), { status: response.status })
  return body
}

export async function login(email, password) {
  try {
    const result = await request('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) })
    if (!result?.user || !result?.token) throw new Error('API is not connected')
    return { ...result, demoMode: false }
  } catch (error) {
    if (error.status && error.status !== 404 && error.status < 500) throw error
    await sleep()
    const account = demoAccounts.find(a => a.email === email.toLowerCase() && a.password === password)
    if (!account) throw new Error('Invalid demo email or password')
    return {
      token: `demo-${account.role}`,
      user: { id: account.role, name: account.name, email: account.email, role: account.role },
      modules: modulesByRole[account.role],
      demoMode: true,
      notice: NETWORK_MESSAGE,
    }
  }
}

const fallback = {
  '/inventory/': () => ({ items: inventory, count: inventory.length }),
  '/quotations/': () => ({ items: quotations, count: quotations.length }),
  '/suppliers/': () => ({ items: suppliers, count: suppliers.length }),
  '/stock/': () => ({ items: stock }),
  '/barcodes/': () => ({ items: inventory.filter(x => x.barcode) }),
  '/fitments/': () => ({ items: fitments, count: fitments.length }),
  '/purchase-orders/': () => ({ items: purchaseOrders, count: purchaseOrders.length }),
  '/receiving/': () => receivingState,
  '/mobile-warehouse/': () => mobileWarehouseState,
  '/warehouses/': () => warehouseState,
  '/reorder/': () => ({ items: reorderSuggestions(), count: reorderSuggestions().length }),
  '/demand-planning/': () => demandPlanningData(),
  '/rfq/': () => ({ items: rfqState.items, count: rfqState.items.length }),
  '/sales-flow/': () => salesFlow,
  '/fulfillment/': () => fulfillmentState,
  '/returns/': () => returnsState,
  '/inventory-control/': () => inventoryControlState,
  '/supplier-performance/': () => supplierPerformanceState,
  '/customers/': () => ({ items: customers, count: customers.length }),
  '/pricing/': () => ({ items: priceRules }),
  '/analytics/': () => analyticsData(),
  '/governance/': () => governanceState,
  '/notifications/': () => notificationState,
  '/copilot/': () => copilotState,
  '/finance/': () => financeState,
  '/warranty/': () => warrantyState,
  '/integrations/': () => integrationsState,
  '/pwa-admin/': () => pwaState,
  '/tenancy/': () => tenantState,
  '/permissions/': () => ({ roles:['admin','manager','sales','store'], actions:['view','create','edit','approve','export'], modules:[] }),
  '/portal/accounts/': () => ({ accounts:[] }),
  '/automation/': () => automationState,
  '/fleet/': () => fleetState,
  '/security/': () => securityState,
  '/documents/': () => documentState,
  '/delivery/': () => deliveryState,
  '/partner-api/': () => partnerApiState,
  '/predictive-fleet/': () => predictiveFleetState,
  '/customer-service/': () => customerServiceState,
  '/saas-billing/': () => billingState,
  '/observability/': () => observabilityState,
  '/inventory-network/': () => inventoryNetworkState,
}

export async function loadEndpoint(path, role) {
  try {
    if (path === '/dashboard/') return { data: await request(path), demoMode: false }
    return { data: await request(path), demoMode: false }
  } catch (error) {
    if (error.status === 401 || error.status === 403) throw error
    await sleep(120)
    const data = path === '/dashboard/' ? mockDashboard(role) : fallback[path]?.()
    if (!data) throw error
    return { data, demoMode: true }
  }
}

function demoPortal(token){
  if(!portalState.tokens[token]){const customer=customers[0];portalState.tokens[token]={token,customer:{id:customer.id,name:customer.name,company:customer.company,email:customer.email},quotes:quotations.filter(q=>q.customer_company===customer.company).map(q=>({...q})),orders:salesFlow.orders.filter(o=>o.customer_company===customer.company).map(o=>({...o,fulfillment_status:o.status})),invoices:fulfillmentState.invoices.filter(i=>i.customer===customer.company).map(i=>({...i}))}}
  return portalState.tokens[token]
}

export async function loadPortal(token) {
  try { return { data: await request(`/portal/?token=${encodeURIComponent(token)}`), demoMode:false } }
  catch (error) { if(error.status && error.status < 500) throw error; await sleep(120); return { data:demoPortal(token), demoMode:true } }
}

export async function portalAction(token, payload) {
  try { return { ...(await request('/portal/', {method:'POST',body:JSON.stringify({token,...payload})})), demoMode:false } }
  catch (error) { if(error.status && error.status < 500) throw error; await sleep(120); const data=demoPortal(token); if(payload.action==='approve_quote'){const q=data.quotes.find(x=>x.id===Number(payload.quote_id));if(q)q.status='approved'} if(payload.action==='repeat_order'){const o=data.orders.find(x=>x.id===Number(payload.order_id));if(o)data.quotes.unshift({id:Date.now(),quote_no:`QT-DEMO-${String(Date.now()).slice(-4)}`,total:o.total,status:'draft',valid_until:new Date(Date.now()+7*86400000).toISOString().slice(0,10)})} return { ...data, demoMode:true } }
}

export async function portalAccountLogin(email, password) {
  const result = await request('/portal/login/', { method:'POST', body: JSON.stringify({ email, password }) })
  return result
}

function createMock(path, payload, role) {
  const id = Date.now()
  if (path === '/customer-service/') {
    if (payload.action === 'ticket') { const item={id,ticket_no:`CS-DEMO-${String(id).slice(-5)}`,customer:payload.customer||'New customer',subject:payload.subject||'New support request',channel:payload.channel||'portal',priority:payload.priority||'normal',status:'open',assignee:payload.assignee||'Unassigned',sla_due:payload.sla_due||'2026-09-24 12:00',last_message:payload.message||'Ticket created from the operations desk.',messages:1}; customerServiceState.tickets.unshift(item); customerServiceState.summary.open_tickets+=1; return {item} }
    const item=customerServiceState.tickets.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Support ticket not found'); if(payload.action==='status')item.status=payload.status||item.status; if(payload.action==='assign')item.assignee=payload.assignee||item.assignee; if(payload.message){item.messages+=1;item.last_message=payload.message;customerServiceState.communications.unshift({id:Date.now(),ticket_no:item.ticket_no,actor:'Demo User',channel:payload.channel||'internal',message:payload.message,created_at:new Date().toISOString()})} return {item}
  }
  if (path === '/saas-billing/') {
    if (payload.action === 'plan') { const tenant=billingState.tenants.find(x=>x.id===Number(payload.id)); if(!tenant)throw new Error('Tenant not found'); tenant.plan=payload.plan; tenant.status='active'; tenant.mrr=billingState.plans.find(x=>x.name===payload.plan)?.price||tenant.mrr; return {item:tenant} }
    if (payload.action === 'retry') { const invoice=billingState.invoices.find(x=>x.id===Number(payload.id)); if(!invoice)throw new Error('Subscription invoice not found'); invoice.status='scheduled'; return {item:invoice} }
    if (payload.action === 'invoice') { const item={id,invoice_no:`SUB-DEMO-${String(id).slice(-5)}`,organization:payload.organization||'Partora Auto Parts India',amount:Number(payload.amount||14999),due:payload.due||'2026-10-01',status:'scheduled'}; billingState.invoices.unshift(item); return {item} }
  }
  if (path === '/observability/') {
    if (payload.action === 'retry') { const item=observabilityState.jobs.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Job not found'); item.status='completed'; item.retries+=1; item.detail='Retry completed successfully'; return {item} }
    if (payload.action === 'resolve') { const item=observabilityState.incidents.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Incident not found'); item.status='resolved'; observabilityState.summary.open_incidents=Math.max(0,observabilityState.summary.open_incidents-1); return {item} }
  }
  if (path === '/inventory-network/') {
    const item=inventoryNetworkState.recommendations.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Transfer recommendation not found'); if(payload.action==='approve')item.status='approved'; if(payload.action==='dismiss')item.status='dismissed'; return {item}
  }
  if (path === '/security/') {
    if (payload.action === 'mfa') { const item=securityState.users.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('User not found'); item.mfa='enabled'; item.risk='low'; return {item} }
    if (payload.action === 'terminate') { const item=securityState.sessions.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Session not found'); item.status='terminated'; securityState.summary.active_sessions=Math.max(0,securityState.summary.active_sessions-1); return {item} }
    if (payload.action === 'resolve') { const item=securityState.alerts.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Security alert not found'); item.status='resolved'; securityState.summary.open_alerts=Math.max(0,securityState.summary.open_alerts-1); return {item} }
    if (payload.action === 'export') return {item:{format:'csv',filename:`partora-security-${new Date().toISOString().slice(0,10)}.csv`,rows:securityState.audit.length}}
  }
  if (path === '/documents/') {
    if (payload.action === 'upload') { const item={id,name:payload.file_name||'supplier-invoice.pdf',file_name:payload.file_name||'supplier-invoice.pdf',supplier:payload.supplier||'New supplier',invoice_no:payload.invoice_no||`INV-DEMO-${String(id).slice(-4)}`,gstin:payload.gstin||'Pending extraction',total:Number(payload.total||0),po_no:payload.po_no||'Pending match',match_status:'pending',confidence:0,status:'processing',uploaded_at:new Date().toISOString(),issue:''}; documentState.documents.unshift(item); documentState.summary.processed_today+=1; documentState.summary.pending_review+=1; return {item} }
    const item=documentState.documents.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Document not found'); if(payload.action==='approve'){item.status='approved';item.match_status='matched';documentState.summary.pending_review=Math.max(0,documentState.summary.pending_review-1)} if(payload.action==='reject'){item.status='rejected';documentState.summary.pending_review=Math.max(0,documentState.summary.pending_review-1)} return {item}
  }
  if (path === '/delivery/') {
    if (payload.action === 'route') { const item={id,route_no:`RT-DEMO-${String(id).slice(-4)}`,driver:payload.driver,vehicle:payload.vehicle,stops:Number(payload.stops||1),completed:0,eta:payload.eta||'15:30',status:'planned',cost:Number(payload.cost||0)}; deliveryState.routes.unshift(item); return {item} }
    const item=deliveryState.shipments.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Shipment not found'); if(payload.action==='status')item.status=payload.status||item.status; if(payload.action==='proof'){item.pod_status='verified';item.proof_at=new Date().toISOString()} return {item}
  }
  if (path === '/partner-api/') {
    if (payload.action === 'key') { const item={id,label:payload.label||'New API key',prefix:`pk_${payload.environment||'test'}_${String(id).slice(-6)}_****`,scopes:payload.scopes||'orders:read',last_used:null,status:'active'}; partnerApiState.keys.unshift(item); partnerApiState.summary.active_keys+=1; return {item} }
    if (payload.action === 'rotate') { const item=partnerApiState.keys.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('API key not found'); item.prefix=`pk_live_rotated_${String(id).slice(-4)}_****`; item.last_used=null; return {item} }
    if (payload.action === 'webhook') { const item={id,event:payload.event||'order.fulfilled',target:payload.target,status:'active',deliveries:0}; partnerApiState.webhooks.unshift(item); partnerApiState.summary.webhooks+=1; return {item} }
  }
  if (path === '/predictive-fleet/') {
    const item=predictiveFleetState.vehicles.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Fleet prediction not found'); if(payload.action==='acknowledge'){item.risk='reviewed';predictiveFleetState.summary.high_risk=Math.max(0,predictiveFleetState.summary.high_risk-1);return {item}} if(payload.action==='service'){item.risk='scheduled';item.prediction='Preventive service scheduled';return {item}} return {item}
  }
  if (path === '/integrations/') {
    if (payload.action === 'connect') { const item={id,name:payload.name||'New connector',type:payload.type||'webhook',status:'connected',last_sync:new Date().toISOString(),records:0}; integrationsState.connections.unshift(item); return {item} }
    if (payload.action === 'test') { const item=integrationsState.connections.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Integration not found'); item.status='connected'; item.last_sync=new Date().toISOString(); return {item} }
    if (payload.action === 'webhook') { const item={id,event:payload.event||'invoice.paid',target:payload.target||'https://client.example/webhooks/partora',status:'active',deliveries:0}; integrationsState.webhooks.unshift(item); return {item} }
  }
  if (path === '/pwa-admin/') {
    if (payload.action === 'resolve') { const item=pwaState.conflicts.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Sync conflict not found'); item.status='resolved'; pwaState.sync.conflicts=Math.max(0,pwaState.sync.conflicts-1); return {item} }
    if (payload.action === 'sync') { pwaState.sync.queued=0; pwaState.sync.synced_today+=1; pwaState.sync.last_sync=new Date().toISOString(); return {item:{sync:pwaState.sync}} }
  }
  if (path === '/tenancy/') {
    if (payload.action === 'invite') { const item={id,name:payload.name,email:payload.email,role:payload.role||'store',branch:payload.branch||'All branches',approval_limit:Number(payload.approval_limit||0),status:'invited'}; tenantState.users.unshift(item); return {item} }
    if (payload.action === 'branch') { const item={id,code:String(payload.code||'').toUpperCase(),name:payload.name,users:0,status:'active'}; tenantState.branches.push(item); tenantState.organization.branches+=1; return {item} }
  }
  if (path === '/automation/') {
    if (payload.action === 'rule') { const item={id,name:payload.name,trigger:payload.trigger,action:payload.rule_action||'Send notification',status:'active',runs:0,last_run:null}; automationState.rules.unshift(item); return {item} }
    const item=automationState.rules.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Automation rule not found'); if(payload.action==='toggle')item.status=item.status==='active'?'paused':'active'; if(payload.action==='run'){item.runs+=1;item.last_run=new Date().toISOString();automationState.runs.unshift({id:Date.now(),rule:item.name,result:'success',detail:'Demo action completed',created_at:new Date().toISOString()})} return {item}
  }
  if (path === '/fleet/') {
    if (payload.action === 'vehicle') { const item={id,registration:payload.registration,customer:payload.customer,make:payload.make,model:payload.model,year:Number(payload.year||2022),mileage:Number(payload.mileage||0),next_service:payload.next_service,status:'healthy'}; fleetState.vehicles.unshift(item); return {item} }
    if (payload.action === 'work_order') { const item={id,order_no:`WO-DEMO-${String(id).slice(-5)}`,registration:payload.registration,customer:payload.customer,technician:payload.technician,status:'scheduled',due_date:payload.due_date,parts_value:Number(payload.parts_value||0),labor_value:Number(payload.labor_value||0),notes:payload.notes||''}; fleetState.work_orders.unshift(item); return {item} }
    const item=fleetState.work_orders.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Work order not found'); item.status=payload.status||item.status; return {item}
  }
  if (path === '/mobile-warehouse/') {
    if (payload.action === 'scan') { const item={id, type:payload.type||'count', reference:payload.reference||`SCAN-${String(id).slice(-5)}`, location:payload.location||'DEL-MAIN', sku:String(payload.sku||'').toUpperCase(), product:inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase())?.name||'Scanned part', quantity:Number(payload.quantity||1), status:'queued', synced:false, created_at:new Date().toISOString()}; mobileWarehouseState.queue.unshift(item); return {item} }
    if (payload.action === 'sync') { mobileWarehouseState.queue.forEach(x=>{if(!x.synced){x.synced=true;x.status='synced'}}); mobileWarehouseState.last_sync=new Date().toISOString(); return {item:{queue:mobileWarehouseState.queue,last_sync:mobileWarehouseState.last_sync}} }
    const item=mobileWarehouseState.queue.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Warehouse task not found'); item.status=payload.action==='complete'?'complete':item.status; return {item}
  }
  if (path === '/notifications/') {
    const item={id,channel:payload.channel||'email',audience:payload.audience||'Operations team',event:payload.event||'Operational alert',status:'queued',detail:payload.detail||'Notification queued for delivery.',created_at:new Date().toISOString()}; notificationState.items.unshift(item); return {item}
  }
  if (path === '/copilot/') {
    const question=String(payload.question||'').trim(); if(!question)throw new Error('Ask the copilot a question')
    const lower=question.toLowerCase(); let answer='Partora recommends reviewing the demand plan, supplier scorecard and action queue before committing inventory or payment changes.'; let source='Operations command center'; if(lower.includes('stock')){answer='RLY-24V4 is the highest stock-out risk. Raise a replenishment plan for 90 units and confirm VoltEdge availability.';source='Demand planning + inventory'}else if(lower.includes('supplier')||lower.includes('delivery')){answer='TorqueLine leads on reliability at 100% on-time in the current demo history. VoltEdge is faster but has an invoice exception to resolve.';source='Supplier intelligence + receiving'}else if(lower.includes('warehouse')){answer='Noida North is at 89% capacity. Move slow-moving BLT-0812 stock to Gurugram before the next inbound receipt.';source='Warehouse control'}else if(lower.includes('invoice')||lower.includes('payment')){answer='VE-INV-8821 needs manager review because its invoice quantity includes damaged units.';source='Finance + three-way matching'} const item={id,question,answer,source,confidence:'Demo analysis',created_at:new Date().toISOString()}; copilotState.messages.unshift(item); return {item}
  }
  if (path === '/finance/') {
    if (payload.action === 'reconcile') { const invoice=financeState.invoices.find(x=>x.id===Number(payload.invoice_id)); if(!invoice)throw new Error('Invoice not found'); const amount=Number(payload.amount||invoice.balance); invoice.paid=Math.min(invoice.total,invoice.paid+amount); invoice.balance=Math.max(0,invoice.total-invoice.paid); invoice.status=invoice.balance===0?'paid':'partial'; financeState.payments.unshift({id,reference:payload.reference||`REC-${String(id).slice(-5)}`,invoice_no:invoice.invoice_no,amount,method:payload.method||'bank',reconciled:true,paid_at:new Date().toISOString().slice(0,10)}); return {item:invoice} }
    if (payload.action === 'export') return {item:{format:payload.format||'csv',filename:`partora-finance-${new Date().toISOString().slice(0,10)}.${payload.format||'csv'}`,rows:financeState.invoices.length}}
  }
  if (path === '/warranty/') {
    const item=warrantyState.claims.find(x=>x.id===Number(payload.id)); if(!item)throw new Error('Warranty claim not found'); if(payload.action==='status')item.status=payload.status||item.status; if(payload.action==='chargeback')item.recovery_amount=Number(payload.amount||item.recovery_amount); return {item}
  }
  if (path === '/governance/') {
    if(payload.action==='request'){const item={id:Date.now(),kind:payload.kind||'purchase',reference:payload.reference,amount:Number(payload.amount||0),status:'pending',requested_by:'Demo User',reviewed_by:null,notes:payload.notes||'',created_at:new Date().toISOString()};governanceState.approvals.unshift(item);return {item}}
    if(['approve','reject'].includes(payload.action)){const item=governanceState.approvals.find(x=>x.id===Number(payload.id));if(!item)throw new Error('Approval not found');item.status=payload.action==='approve'?'approved':'rejected';item.reviewed_by='Demo Manager';return {item}}
    if(payload.action==='read'){const item=governanceState.notifications.find(x=>x.id===Number(payload.id));if(item)item.read=true;return {item:{id:Number(payload.id),read:true}}}
  }
  if (path === '/pricing/') {
    if(payload.action==='preview'){const product=inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found');const type=payload.customer_type||'retail';const qty=Math.max(1,Number(payload.quantity||1));const base=type==='dealer'?(product.dealer_price||product.price):(['fleet','workshop'].includes(type)?(product.wholesale_price||product.price):product.price);const rule=priceRules.filter(r=>r.active&&r.customer_type===type&&r.min_qty<=qty).sort((a,b)=>b.min_qty-a.min_qty)[0];const discount=rule?.discount_percent||0;const unit=Math.round(base*(1-discount/100)*100)/100;return {item:{sku:product.sku,name:product.name,customer_type:type,quantity:qty,base_price:base,discount_percent:discount,unit_price:unit,line_total:unit*qty,margin_percent:product.cost_price?Math.round((unit-product.cost_price)/unit*1000)/10:null,rule:rule?.name||null}}}
    const item={id:Date.now(),name:payload.name,customer_type:payload.customer_type||'dealer',min_qty:Number(payload.min_qty||1),discount_percent:Number(payload.discount_percent||0),active:true};priceRules.push(item);return {item}
  }
  if (path === '/customers/') {
    const item={id:Date.now(),name:payload.name,company:payload.company||'',email:payload.email||'',phone:payload.phone||'',customer_type:payload.customer_type||'retail',credit_limit:Number(payload.credit_limit||0),payment_terms_days:Number(payload.payment_terms_days||0),outstanding_balance:Number(payload.outstanding_balance||0),notes:payload.notes||''};customers.unshift(item);return {item}
  }
  if (path === '/sales-flow/') {
    if(payload.action==='convert_quote'){const q=quotations.find(x=>x.id===Number(payload.quote_id));if(!q)throw new Error('Quote not found');let item=salesFlow.orders.find(x=>x.quote_no===q.quote_no);if(!item){item={id:Date.now(),order_no:`SO-DEMO-${String(Date.now()).slice(-4)}`,quote_no:q.quote_no,customer_name:q.customer_name,customer_company:q.customer_company,total:q.total,status:'confirmed',invoice_no:null,created_at:new Date().toISOString()};salesFlow.orders.unshift(item)}return {item,action:'convert_quote'}}
    if(payload.action==='invoice'){const o=salesFlow.orders.find(x=>x.id===Number(payload.order_id));if(!o)throw new Error('Order not found');let item=salesFlow.invoices.find(x=>x.order_no===o.order_no);if(!item){const d=new Date();d.setDate(d.getDate()+30);item={id:Date.now(),invoice_no:`INV-DEMO-${String(Date.now()).slice(-4)}`,order_no:o.order_no,customer:o.customer_company||o.customer_name,total:o.total,status:'issued',due_date:d.toISOString().slice(0,10)};salesFlow.invoices.unshift(item);o.invoice_no=item.invoice_no}return {item,action:'invoice'}}
  }
  if (path === '/fulfillment/') {
    const order=fulfillmentState.orders.find(x=>x.id===Number(payload.order_id)); if(!order)throw new Error('Order not found')
    if(payload.action==='reserve'){order.reserved=true;order.fulfillment_status='picking';return {item:order}}
    if(payload.action==='status'){order.fulfillment_status=payload.status; if(payload.status==='dispatched')order.status='fulfilled'; return {item:order}}
    if(payload.action==='payment'){
      let invoice=fulfillmentState.invoices.find(x=>x.order_no===order.order_no); if(!invoice){invoice={id:Date.now(),invoice_no:`INV-DEMO-${String(Date.now()).slice(-4)}`,order_no:order.order_no,customer:order.customer_company||order.customer_name,total:order.total,paid:0,balance:order.total,status:'issued',due_date:new Date(Date.now()+30*86400000).toISOString().slice(0,10)};fulfillmentState.invoices.unshift(invoice);order.invoice_no=invoice.invoice_no}
      invoice.paid+=Number(payload.amount||0);invoice.balance=Math.max(0,invoice.total-invoice.paid);invoice.status=invoice.balance===0?'paid':'partial';return {item:order,invoice}
    }
  }
  if (path === '/returns/') {
    if(payload.action==='create'){const product=inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found');const item={id:Date.now(),return_no:`RMA-DEMO-${String(Date.now()).slice(-4)}`,order_no:payload.order_no||null,sku:product.sku,product:product.name,customer_name:payload.customer_name||'Walk-in customer',quantity:Number(payload.quantity||1),reason:payload.reason,warranty_expires:payload.warranty_expires||null,status:'requested',resolution:'',inspection_notes:'',refund_amount:Number(payload.refund_amount||0),stock_restocked:false,created_at:new Date().toISOString()};returnsState.items.unshift(item);return {item}}
    const item=returnsState.items.find(x=>x.id===Number(payload.id));if(!item)throw new Error('Return not found');item.status=payload.status||item.status;item.resolution=payload.resolution||item.resolution;item.inspection_notes=payload.inspection_notes||item.inspection_notes;item.stock_restocked=item.status==='resolved'&&item.resolution==='restock';return {item}
  }
  if (path === '/inventory-control/') {
    if(payload.action==='count'){const product=inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found');const expected=Number(payload.expected_qty??product.stock_qty);const counted=Number(payload.counted_qty||0);const item={id:Date.now(),reference:`CNT-DEMO-${String(Date.now()).slice(-4)}`,warehouse:payload.warehouse||null,status:'submitted',notes:payload.notes||'',counted_by:'Demo User',created_at:new Date().toISOString(),lines:[{sku:product.sku,product:product.name,expected_qty:expected,counted_qty:counted,variance:counted-expected}]};inventoryControlState.counts.unshift(item);return {item}}
    if(payload.action==='approve'){const item=inventoryControlState.counts.find(x=>x.id===Number(payload.id));if(!item)throw new Error('Count not found');item.status='approved';item.lines.forEach(line=>{const product=inventory.find(x=>x.sku===line.sku);if(product){product.stock_qty=line.counted_qty;product.stock_status=product.stock_qty<=product.reorder_level?'low':'healthy'}});return {item}}
    if(payload.action==='lot'){const product=inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found');const item={id:Date.now(),sku:product.sku,product:product.name,lot_no:payload.lot_no,serial_no:payload.serial_no||'',quantity:Number(payload.quantity||1),warehouse:payload.warehouse||null,expiry_date:payload.expiry_date||null};inventoryControlState.lots.unshift(item);return {item}}
  }
  if (path === '/supplier-performance/') {
    const product=inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase());const supplier=suppliers.find(x=>x.name===payload.supplier);if(!product||!supplier)throw new Error('Supplier or SKU not found');const item={id:Date.now(),supplier:supplier.name,sku:product.sku,product:product.name,unit_cost:Number(payload.unit_cost||product.cost_price||product.price),captured_at:new Date().toISOString()};supplierPerformanceState.prices.unshift(item);return {item}
  }
  if (path === '/demand-planning/') {
    const product = inventory.find(x => x.sku === String(payload.sku || '').toUpperCase())
    if (payload.action === 'request') {
      if (!product) throw new Error('SKU not found')
      const existing = demandPlanningState.plans.find(x => x.sku === product.sku && ['pending', 'approved', 'ordered'].includes(x.status))
      if (existing) return { item: existing }
      const item = { id:Date.now(), plan_id:Date.now(), sku:product.sku, product:product.name, supplier:product.supplier, average_daily_demand:0, window_days:90, horizon_days:30, available_qty:product.stock_qty, safety_stock:product.reorder_level, reorder_point:product.reorder_level, recommended_qty:Number(payload.quantity || product.reorder_qty || 25), unit_cost:product.cost_price || product.price, estimated_cost:Number(payload.quantity || product.reorder_qty || 25) * (product.cost_price || product.price), projected_stockout:null, expected_date:null, status:'pending' }
      demandPlanningState.plans.unshift(item)
      return { item }
    }
    const item = demandPlanningState.plans.find(x => x.id === Number(payload.id))
    if (!item) throw new Error('Purchase plan not found')
    if (payload.action === 'approve') { item.status = 'ordered'; item.po_no = `PO-FORECAST-${String(Date.now()).slice(-4)}` }
    if (payload.action === 'reject') item.status = 'rejected'
    return { item }
  }
  if (path === '/rfq/') {
    if (payload.action === 'create') {
      const product = inventory.find(x => x.sku === String(payload.sku || '').toUpperCase())
      if (!product) throw new Error('SKU not found')
      const names = String(payload.suppliers || '').split(',').map(x => x.trim()).filter(Boolean)
      const selectedSuppliers = (names.length ? suppliers.filter(x => names.includes(x.name)) : suppliers).slice(0, 5)
      if (selectedSuppliers.length < 2) throw new Error('Select at least two suppliers')
      const item = { id:Date.now(), rfq_no:`RFQ-DEMO-${String(Date.now()).slice(-4)}`, sku:product.sku, product:product.name, quantity:Number(payload.quantity || 1), needed_by:payload.needed_by || null, status:'sent', purchase_plan_id:null, notes:payload.notes || '', requested_by:'Demo User', created_at:new Date().toISOString(), offers:selectedSuppliers.map((supplier,index) => ({ id:Date.now()+index, supplier:supplier.name, supplier_rating:supplier.rating, unit_price:0, total:0, lead_time_days:supplier.lead_time_days, moq:1, available_qty:0, payment_terms:'', status:'pending', notes:'', score:0, is_recommended:false })) }
      rfqState.items.unshift(item); return { item }
    }
    const rfq = rfqState.items.find(x => x.id === Number(payload.id) || x.offers.some(offer => offer.id === Number(payload.offer_id)))
    if (!rfq) throw new Error('RFQ not found')
    if (payload.action === 'quote') {
      const offer = rfq.offers.find(x => x.id === Number(payload.offer_id)); if (!offer) throw new Error('Offer not found')
      offer.unit_price=Number(payload.unit_price||0); offer.total=offer.unit_price*rfq.quantity; offer.lead_time_days=Number(payload.lead_time_days||offer.lead_time_days); offer.moq=Number(payload.moq||1); offer.available_qty=Number(payload.available_qty||0); offer.payment_terms=payload.payment_terms||''; offer.notes=payload.notes||''; offer.status='received'; rfq.status='quoted'; return { item:rfq }
    }
    if (payload.action === 'select') {
      const offer = rfq.offers.find(x => x.id === Number(payload.offer_id)); if (!offer || offer.status !== 'received') throw new Error('Record a supplier quote first')
      offer.status='selected'; rfq.offers.filter(x => x.id !== offer.id).forEach(x => { x.status='rejected' }); rfq.status='selected'; rfq.recommended_offer_id=offer.id; rfq.recommended_supplier=offer.supplier; offer.po_no=`PO-RFQ-${String(Date.now()).slice(-4)}`; purchaseOrders.unshift({id:Date.now(),po_no:offer.po_no,supplier:offer.supplier,status:'approved',expected_date:rfq.needed_by,total:offer.total,created_by:'Demo Manager',line_count:1,received_lines:0}); return { item:rfq, po_no:offer.po_no }
    }
    if (payload.action === 'close') { rfq.status='closed'; return { item:rfq } }
  }
  if (path === '/portal/issue/') {
    const customer=customers.find(x=>x.id===Number(payload.customer_id));if(!customer)throw new Error('Customer not found');const token=`demo-${customer.id}-${Date.now()}`;const data={token,customer:{id:customer.id,name:customer.name,company:customer.company,email:customer.email},quotes:quotations.filter(q=>q.customer_company===customer.company).map(q=>({...q})),orders:salesFlow.orders.filter(o=>o.customer_company===customer.company).map(o=>({...o,fulfillment_status:o.status})),invoices:[]};portalState.tokens[token]=data;return {item:{token,customer:customer.company||customer.name,expires_at:new Date(Date.now()+30*86400000).toISOString(),portal_path:`/portal/${token}`},portal:data}
  }
  if (path === '/reorder/') {
    const product=inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found')
    const item={id:Date.now(),po_no:`PO-REORDER-${String(Date.now()).slice(-4)}`,sku:product.sku,supplier:product.supplier,quantity:Number(payload.quantity||product.reorder_qty||25),status:'approved'};purchaseOrders.unshift({...item,expected_date:null,total:item.quantity*product.price,line_count:1,received_lines:0,created_by:'Demo User'});return {item}
  }
  if (path === '/warehouses/') {
    if(payload.action==='warehouse'){const item={id:Date.now(),code:String(payload.code||'').toUpperCase(),name:payload.name,address:payload.address||'',sku_count:0,units:0};warehouseState.warehouses.push(item);return {item}}
    const item={id:Date.now(),reference:`TR-DEMO-${String(Date.now()).slice(-4)}`,from_warehouse:String(payload.from_warehouse||'').toUpperCase(),to_warehouse:String(payload.to_warehouse||'').toUpperCase(),sku:String(payload.sku||'').toUpperCase(),product:inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase())?.name||'Demo part',quantity:Number(payload.quantity||1),status:'completed',created_at:new Date().toISOString()};warehouseState.transfers.unshift(item);return {item}
  }
  if (path === '/purchase-orders/') {
    if(payload.action==='receive'){const po=purchaseOrders.find(x=>x.id===Number(payload.id));if(!po)throw new Error('PO not found');po.status='received';po.received_lines=po.line_count;return {item:po}}
    const product=inventory.find(x=>x.sku.toUpperCase()===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found')
    const item={id:Date.now(),po_no:`PO-DEMO-${String(Date.now()).slice(-4)}`,supplier:payload.supplier,status:payload.status||'draft',expected_date:payload.expected_date||null,total:Number(payload.quantity||1)*Number(payload.unit_cost||product.price),created_by:'Demo User',line_count:1,received_lines:0};purchaseOrders.unshift(item);return {item}
  }
  if (path === '/receiving/') {
    const order=receivingState.orders.find(x=>x.id===Number(payload.po_id)); if(!order)throw new Error('Purchase order not found')
    if(payload.action==='receive'){
      const line=order.items.find(x=>x.id===Number(payload.lines?.[0]?.item_id)); if(!line)throw new Error('Purchase order line not found')
      const accepted=Number(payload.lines[0].accepted_qty||0), damaged=Number(payload.lines[0].damaged_qty||0); if(accepted+damaged>line.remaining_qty)throw new Error('Receipt exceeds remaining quantity')
      line.accepted_qty+=accepted; line.damaged_qty+=damaged; line.received_qty+=accepted+damaged; line.remaining_qty=line.ordered_qty-line.received_qty; order.accepted_qty+=accepted; order.damaged_qty+=damaged; order.remaining_qty-=accepted+damaged; order.status=order.remaining_qty===0?'received':'partial'; const product=inventory.find(x=>x.sku===line.sku); if(product){product.stock_qty+=accepted;product.stock_status=product.stock_qty<=product.reorder_level?'low':'healthy'} return {item:order}
    }
    if(payload.action==='invoice'){
      const total=Number(payload.total||0), qty=Number(payload.invoice_qty||0), expected=order.ordered_qty?order.total/order.ordered_qty*qty:0; const invoice={id:Date.now(),invoice_no:payload.invoice_no,invoice_date:payload.invoice_date||new Date().toISOString().slice(0,10),invoice_qty:qty,subtotal:Number(payload.subtotal||total),tax:Number(payload.tax||0),total,status:qty>0&&qty<=order.accepted_qty&&Math.abs(total-expected)<.01?'matched':'exception',notes:payload.notes||'',created_by:'Demo User'}; order.invoices.unshift(invoice); return {item:order,invoice}
    }
    if(payload.action==='approve'){const invoice=order.invoices.find(x=>x.id===Number(payload.invoice_id));if(!invoice)throw new Error('Invoice not found');invoice.status='approved';return {item:{id:invoice.id,invoice_no:invoice.invoice_no,status:invoice.status}}}
  }
  if (path === '/fitments/') {
    if (payload.action === 'decode_vin') {
      const vin = String(payload.vin || '').replace(/\s+/g, '').toUpperCase(); const vehicle = vinVehicles[vin] || (vin.length >= 8 ? { make:'Maruti Suzuki', model:'Swift', year:2022, variant:'Petrol / AMT', engine:'1.2L', fuel:'Petrol' } : null)
      if (!vehicle) throw new Error('Enter a valid 8+ character VIN')
      const matches = fitments.filter(x => x.make === vehicle.make && x.model === vehicle.model && vehicle.year >= x.year_from && vehicle.year <= x.year_to).map(x => ({...x, stock_qty:inventory.find(p=>p.sku===x.sku)?.stock_qty||0, stock_status:inventory.find(p=>p.sku===x.sku)?.stock_status||'unknown', fitment_confidence:x.oem_number?'98%':'92%'}))
      return { item:{vin,vehicle,matches} }
    }
    const product = inventory.find(x => x.sku.toUpperCase() === String(payload.sku || '').toUpperCase())
    if (!product) throw new Error('SKU not found in demo inventory')
    const item={id:Date.now(),sku:product.sku,product:product.name,make:payload.make,model:payload.model,year_from:Number(payload.year_from),year_to:Number(payload.year_to||payload.year_from),variant:payload.variant||'',engine:payload.engine||'',oem_number:payload.oem_number||''}
    fitments.unshift(item); return { item }
  }
  if (path === '/barcodes/') {
    const product = inventory.find(x => x.sku.toUpperCase() === String(payload.sku || '').toUpperCase())
    if (!product) throw new Error('SKU not found in demo inventory')
    product.barcode = String(payload.barcode || '').trim() || `PARTORA-${product.sku}`
    return { item: product }
  }
  if (path === '/inventory/') {
    const stockQty = Number(payload.stock_qty || 0)
    const reorder = Number(payload.reorder_level || 10)
    const item = {
      id, sku: String(payload.sku || '').toUpperCase(), name: payload.name, brand: payload.brand,
      category: payload.category, supplier: payload.supplier || 'Unassigned', price: Number(payload.price || 0),
      stock_qty: stockQty, reorder_level: reorder, stock_status: stockQty <= 0 ? 'out' : stockQty <= reorder ? 'low' : 'healthy',
      bin_location: payload.bin_location || '—',
    }
    inventory.unshift(item); return { item }
  }
  if (path === '/quotations/') {
    const account = demoAccounts.find(a => a.role === role)
    const item = {
      id, quote_no: `QT-DEMO-${String(id).slice(-5)}`, customer_name: payload.customer_name,
      customer_company: payload.customer_company || '', total: Number(payload.total || 0), status: payload.status || 'draft',
      valid_until: payload.valid_until, created_by: account?.name || 'Demo User',
    }
    quotations.unshift(item); return { item }
  }
  if (path === '/suppliers/') {
    const item = {
      id, name: payload.name, contact_name: payload.contact_name || '', phone: payload.phone || '', email: payload.email || '',
      lead_time_days: Number(payload.lead_time_days || 3), rating: Number(payload.rating || 4), active: true,
    }
    suppliers.unshift(item); return { item }
  }
  if (path === '/stock/') {
    const product = inventory.find(x => x.sku.toUpperCase() === String(payload.sku || '').toUpperCase())
    if (!product) throw new Error('SKU not found in demo inventory')
    const qty = Math.abs(Number(payload.quantity || 0))
    if (!qty) throw new Error('Quantity must be greater than zero')
    if (payload.type === 'out') product.stock_qty = Math.max(0, product.stock_qty - qty)
    else if (payload.type === 'adjustment') product.stock_qty = qty
    else product.stock_qty += qty
    product.stock_status = product.stock_qty <= 0 ? 'out' : product.stock_qty <= product.reorder_level ? 'low' : 'healthy'
    const item = { id, sku: product.sku, product: product.name, type: payload.type || 'in', quantity: qty, reference: payload.reference || 'DEMO', created_at: new Date().toISOString() }
    stock.unshift(item); return { item }
  }
  throw new Error('Unsupported demo action')
}

export async function createEndpoint(path, payload, role) {
  try {
    const result = await request(path, { method: 'POST', body: JSON.stringify(payload) })
    if (!result?.item) throw new Error('API is not connected')
    return { ...result, demoMode: false }
  } catch (error) {
    if (error.status && error.status !== 404 && error.status < 500) throw error
    await sleep(140)
    return { ...createMock(path, payload, role), demoMode: true }
  }
}
