export const demoAccounts = [
  { email: 'admin@partora.demo', password: 'demo123', name: 'Aarav Admin', role: 'admin' },
  { email: 'manager@partora.demo', password: 'demo123', name: 'Meera Manager', role: 'manager' },
  { email: 'sales@partora.demo', password: 'demo123', name: 'Rohan Sales', role: 'sales' },
  { email: 'store@partora.demo', password: 'demo123', name: 'Kabir Store', role: 'store' },
]

export const modulesByRole = {
  admin: ['dashboard', 'inventory', 'quotations', 'suppliers', 'stock', 'barcodes', 'fitments', 'purchase_orders', 'receiving', 'warehouses', 'reorder', 'demand_planning', 'rfq', 'sales_flow', 'fulfillment', 'crm', 'pricing', 'analytics', 'governance'],
  manager: ['dashboard', 'inventory', 'quotations', 'suppliers', 'stock', 'barcodes', 'fitments', 'purchase_orders', 'receiving', 'warehouses', 'reorder', 'demand_planning', 'rfq', 'sales_flow', 'fulfillment', 'crm', 'pricing', 'analytics', 'governance'],
  sales: ['dashboard', 'inventory', 'quotations', 'barcodes', 'fitments', 'sales_flow', 'fulfillment', 'crm', 'pricing', 'analytics', 'governance'],
  store: ['dashboard', 'inventory', 'stock', 'barcodes', 'fitments', 'purchase_orders', 'receiving', 'warehouses', 'reorder', 'demand_planning', 'rfq', 'fulfillment', 'governance'],
}

export const inventory = [
  { id: 1, sku: 'BRK-1048', name: 'Ceramic Brake Pad Set', brand: 'RoadShield', category: 'auto', supplier: 'TorqueLine Components', price: 2450, cost_price: 1519, wholesale_price: 2156, dealer_price: 2009, stock_qty: 38, reorder_level: 12, reorder_qty: 30, stock_status: 'healthy', bin_location: 'A-04-12', barcode: '890100010481' },
  { id: 2, sku: 'FLT-2210', name: 'Engine Oil Filter', brand: 'MotoPure', category: 'auto', supplier: 'TorqueLine Components', price: 420, cost_price: 260, wholesale_price: 370, dealer_price: 344, stock_qty: 8, reorder_level: 15, reorder_qty: 40, stock_status: 'low', bin_location: 'A-02-03', barcode: '890100022102' },
  { id: 3, sku: 'BLT-0812', name: 'Hex Bolt M8 × 20 mm', brand: 'ForgeFast', category: 'hardware', supplier: 'ForgeFast Hardware', price: 12, cost_price: 7, wholesale_price: 11, dealer_price: 10, stock_qty: 640, reorder_level: 120, reorder_qty: 250, stock_status: 'healthy', bin_location: 'H-11-08', barcode: '890100008123' },
  { id: 4, sku: 'BRG-6204', name: 'Deep Groove Bearing 6204', brand: 'AxisPro', category: 'hardware', supplier: 'ForgeFast Hardware', price: 310, cost_price: 192, wholesale_price: 273, dealer_price: 254, stock_qty: 5, reorder_level: 18, reorder_qty: 50, stock_status: 'low', bin_location: 'H-03-14', barcode: '890100062043' },
  { id: 5, sku: 'MCB-C32', name: '32A C-Curve MCB', brand: 'VoltEdge', category: 'electrical', supplier: 'VoltEdge Electricals', price: 690, cost_price: 428, wholesale_price: 607, dealer_price: 566, stock_qty: 72, reorder_level: 20, reorder_qty: 50, stock_status: 'healthy', bin_location: 'E-08-02', barcode: '890100032003' },
  { id: 6, sku: 'RLY-24V4', name: '24V 4-Pin Automotive Relay', brand: 'VoltEdge', category: 'electrical', supplier: 'VoltEdge Electricals', price: 180, cost_price: 112, wholesale_price: 158, dealer_price: 148, stock_qty: 0, reorder_level: 16, reorder_qty: 40, stock_status: 'out', bin_location: 'E-05-09', barcode: '890100024004' },
  { id: 7, sku: 'HLM-H7', name: 'H7 LED Headlamp Pair', brand: 'NightArc', category: 'auto', supplier: 'VoltEdge Electricals', price: 1650, cost_price: 1023, wholesale_price: 1452, dealer_price: 1353, stock_qty: 26, reorder_level: 10, reorder_qty: 25, stock_status: 'healthy', bin_location: 'A-09-01', barcode: '890100000707' },
  { id: 8, sku: 'CBL-25R', name: '2.5 sq mm Copper Cable Roll', brand: 'VoltEdge', category: 'electrical', supplier: 'VoltEdge Electricals', price: 3250, cost_price: 2015, wholesale_price: 2860, dealer_price: 2665, stock_qty: 14, reorder_level: 8, reorder_qty: 20, stock_status: 'healthy', bin_location: 'E-12-04', barcode: '890100025007' },
]

export const quotations = [
  { id: 1, quote_no: 'QT-260921-104', customer_name: 'Anil Verma', customer_company: 'Metro Garage', total: 18450, status: 'sent', valid_until: '2026-09-28', created_by: 'Rohan Sales' },
  { id: 2, quote_no: 'QT-260921-103', customer_name: 'Priya Nair', customer_company: 'Northline Repairs', total: 32600, status: 'approved', valid_until: '2026-10-01', created_by: 'Meera Manager' },
  { id: 3, quote_no: 'QT-260920-099', customer_name: 'Imran Sheikh', customer_company: 'Rapid Fleet Care', total: 12780, status: 'draft', valid_until: '2026-09-26', created_by: 'Rohan Sales' },
  { id: 4, quote_no: 'QT-260919-091', customer_name: 'Vikas Jain', customer_company: 'Jain Electrical Works', total: 48500, status: 'sent', valid_until: '2026-09-25', created_by: 'Aarav Admin' },
]

export const suppliers = [
  { id: 1, name: 'TorqueLine Components', contact_name: 'Neha Rao', phone: '+91 98100 21001', email: 'sales@torqueline.demo', lead_time_days: 3, rating: 4.8, active: true },
  { id: 2, name: 'VoltEdge Electricals', contact_name: 'Sameer Khan', phone: '+91 98100 21002', email: 'trade@voltedge.demo', lead_time_days: 2, rating: 4.7, active: true },
  { id: 3, name: 'ForgeFast Hardware', contact_name: 'Pooja Shah', phone: '+91 98100 21003', email: 'orders@forgefast.demo', lead_time_days: 5, rating: 4.5, active: true },
]

export const stock = [
  { id: 1, sku: 'BRK-1048', product: 'Ceramic Brake Pad Set', type: 'in', quantity: 24, reference: 'GRN-8842', created_at: '2026-09-21T08:20:00+05:30' },
  { id: 2, sku: 'FLT-2210', product: 'Engine Oil Filter', type: 'out', quantity: 12, reference: 'INV-5901', created_at: '2026-09-21T09:05:00+05:30' },
  { id: 3, sku: 'BRG-6204', product: 'Deep Groove Bearing 6204', type: 'out', quantity: 4, reference: 'INV-5897', created_at: '2026-09-21T09:42:00+05:30' },
  { id: 4, sku: 'MCB-C32', product: '32A C-Curve MCB', type: 'in', quantity: 50, reference: 'GRN-8838', created_at: '2026-09-21T10:18:00+05:30' },
]

export function mockDashboard(role) {
  return {
    role,
    metrics: {
      products: inventory.length,
      low_stock: inventory.filter(x => x.stock_status !== 'healthy').length,
      open_quotes: quotations.filter(x => ['draft', 'sent'].includes(x.status)).length,
      suppliers: suppliers.length,
      catalog_value: inventory.reduce((sum, item) => sum + item.price * Math.max(item.stock_qty, 0), 0),
    },
    recent_quotes: quotations.slice(0, 4),
    low_stock_items: inventory.filter(x => x.stock_status !== 'healthy'),
  }
}

export const fitments = [
  { id:1, sku:'BRK-1048', product:'Ceramic Brake Pad Set', make:'Maruti Suzuki', model:'Swift', year_from:2018, year_to:2026, variant:'Petrol / AMT', engine:'1.2L', oem_number:'55810M68P00' },
  { id:2, sku:'FLT-2210', product:'Engine Oil Filter', make:'Hyundai', model:'i20', year_from:2020, year_to:2026, variant:'Petrol', engine:'1.2L', oem_number:'26300-35505' },
  { id:3, sku:'HLM-H7', product:'H7 LED Headlamp Pair', make:'Universal', model:'H7 socket', year_from:2005, year_to:2026, variant:'12V', engine:'', oem_number:'H7' },
]

export const vinVehicles = {
  'MA3EJKD1S00A12345': { make:'Maruti Suzuki', model:'Swift', year:2022, variant:'Petrol / AMT', engine:'1.2L', fuel:'Petrol' },
  'MALBB51BLNM123456': { make:'Hyundai', model:'i20', year:2023, variant:'Sportz', engine:'1.2L', fuel:'Petrol' },
}

export const purchaseOrders = [
  { id:1, po_no:'PO-260921-A12F', supplier:'TorqueLine Components', status:'ordered', expected_date:'2026-09-24', total:25200, created_by:'Meera Manager', line_count:3, received_lines:0 },
  { id:2, po_no:'PO-260920-90BD', supplier:'VoltEdge Electricals', status:'partial', expected_date:'2026-09-23', total:44100, created_by:'Aarav Admin', line_count:4, received_lines:2 },
]

export const receivingState = {
  summary: { purchase_orders: 2, awaiting_receipt: 2, damaged_units: 1, invoice_exceptions: 1 },
  orders: [
    { id:1, po_no:'PO-260921-A12F', supplier:'TorqueLine Components', status:'ordered', expected_date:'2026-09-24', total:25200, ordered_qty:60, accepted_qty:0, damaged_qty:0, remaining_qty:60, items:[{id:101,sku:'FLT-2210',product:'Engine Oil Filter',ordered_qty:60,received_qty:0,accepted_qty:0,damaged_qty:0,remaining_qty:60,unit_cost:245}], invoices:[] },
    { id:2, po_no:'PO-260920-90BD', supplier:'VoltEdge Electricals', status:'partial', expected_date:'2026-09-23', total:44100, ordered_qty:100, accepted_qty:48, damaged_qty:2, remaining_qty:50, items:[{id:102,sku:'HLM-H7',product:'H7 LED Headlamp Pair',ordered_qty:100,received_qty:50,accepted_qty:48,damaged_qty:2,remaining_qty:50,unit_cost:441}], invoices:[{id:201,invoice_no:'VE-INV-8821',invoice_date:'2026-09-22',invoice_qty:50,subtotal:22050,tax:0,total:22050,status:'exception',notes:'Invoice quantity includes damaged units',created_by:'Kabir Store'}] },
  ],
  invoices: [],
}

export const warehouseState = {
  warehouses: [
    { id:1, code:'DEL-MAIN', name:'Delhi Main Warehouse', address:'Okhla Industrial Area, Delhi', sku_count:8, units:781, capacity:1000, capacity_pct:78, status:'healthy' },
    { id:2, code:'GUR-SAT', name:'Gurugram Satellite Store', address:'Udyog Vihar, Gurugram', sku_count:5, units:214, capacity:300, capacity_pct:71, status:'healthy' },
    { id:3, code:'NOI-NTH', name:'Noida North Store', address:'Sector 63, Noida', sku_count:4, units:133, capacity:150, capacity_pct:89, status:'watch' },
  ],
  transfers: [
    { id:1, reference:'TR-260921-2A7F', from_warehouse:'DEL-MAIN', to_warehouse:'GUR-SAT', sku:'BRK-1048', product:'Ceramic Brake Pad Set', quantity:12, status:'completed', created_at:'2026-09-21T10:25:00+05:30' },
  ],
}

export function reorderSuggestions(){
  return inventory.filter(p=>p.stock_qty<=p.reorder_level).map(p=>({id:p.id,sku:p.sku,name:p.name,supplier:p.supplier,stock_qty:p.stock_qty,reorder_level:p.reorder_level,suggested_qty:Math.max(p.reorder_qty||25,p.reorder_level*2-p.stock_qty),unit_price:p.price,severity:p.stock_qty<=0?'out':'low'}))
}

export const salesFlow = {
  orders: [
    { id:1, order_no:'SO-260921-41BC', quote_no:'QT-260921-103', customer_name:'Priya Nair', customer_company:'Northline Repairs', total:32600, status:'confirmed', invoice_no:null, created_at:'2026-09-21T11:10:00+05:30' },
  ],
  invoices: [],
}

export const fulfillmentState = {
  orders: [
    { id:1, order_no:'SO-260921-41BC', quote_no:'QT-260921-103', customer_name:'Priya Nair', customer_company:'Northline Repairs', total:32600, status:'confirmed', fulfillment_status:'confirmed', shipping_address:'Sector 18, Gurugram', invoice_no:null, reserved:false, items:[{id:1,sku:'BRK-1048',product:'Ceramic Brake Pad Set',quantity:4,unit_price:2450,line_total:9800,available:38},{id:2,sku:'HLM-H7',product:'H7 LED Headlamp Pair',quantity:2,unit_price:1650,line_total:3300,available:26}], created_at:'2026-09-21T11:10:00+05:30' },
  ],
  invoices: [],
}

export const returnsState = {
  items: [{ id:1, return_no:'RMA-260921-7A2C', order_no:'SO-260921-41BC', sku:'BRK-1048', product:'Ceramic Brake Pad Set', customer_name:'Northline Repairs', quantity:1, reason:'Fitment issue reported after installation', warranty_expires:'2027-09-21', status:'requested', resolution:'', inspection_notes:'', refund_amount:0, stock_restocked:false, created_at:'2026-09-21T12:05:00+05:30' }],
}

export const inventoryControlState = {
  availability: inventory.map(x => ({ id:x.id, sku:x.sku, product:x.name, stock_qty:x.stock_qty, reserved_qty:0, available_qty:x.stock_qty, status:x.stock_status })),
  counts: [{ id:1, reference:'CNT-260921-9B20', warehouse:'DEL-MAIN', status:'submitted', notes:'End-of-day brake aisle count', counted_by:'Kabir Store', created_at:'2026-09-21T17:20:00+05:30', lines:[{sku:'BRK-1048',product:'Ceramic Brake Pad Set',expected_qty:38,counted_qty:37,variance:-1}] }],
  lots: [{ id:1, sku:'BRK-1048', product:'Ceramic Brake Pad Set', lot_no:'RS-2026-08', serial_no:'', quantity:20, warehouse:'DEL-MAIN', expiry_date:null }],
}

export const supplierPerformanceState = {
  suppliers: suppliers.map(s => ({ id:s.id, name:s.name, lead_time_days:s.lead_time_days, rating:s.rating, po_count:2, received_count:1, on_time_rate:100, fill_rate:92, latest_cost:null })),
  plans: reorderSuggestions().map(x => ({ sku:x.sku, product:x.name, supplier:x.supplier, stock_qty:x.stock_qty, reorder_level:x.reorder_level, suggested_qty:x.suggested_qty, lead_time_days:suppliers.find(s=>s.name===x.supplier)?.lead_time_days||3, expected_stockout:'2026-09-24' })),
  prices: [{ id:1, supplier:'TorqueLine Components', sku:'BRK-1048', product:'Ceramic Brake Pad Set', unit_cost:1519, captured_at:'2026-09-21T09:00:00+05:30' }],
  contracts: [
    { id:1, supplier:'TorqueLine Components', contract_no:'TL-2026-04', expires_on:'2026-10-15', payment_terms:'Net 30', annual_value:1850000, status:'expiring' },
    { id:2, supplier:'VoltEdge Electricals', contract_no:'VE-2026-02', expires_on:'2027-02-28', payment_terms:'Net 15', annual_value:1260000, status:'active' },
    { id:3, supplier:'ForgeFast Hardware', contract_no:'FF-2025-09', expires_on:'2026-11-30', payment_terms:'Net 45', annual_value:780000, status:'review' },
  ],
}

const demandHistory = { 'BRK-1048': 30, 'FLT-2210': 72, 'BLT-0812': 540, 'BRG-6204': 42, 'MCB-C32': 50, 'RLY-24V4': 90, 'HLM-H7': 24, 'CBL-25R': 18 }

export const demandPlanningState = { plans: [] }

export function demandPlanningData() {
  const today = new Date()
  const items = inventory.map(product => {
    const supplier = suppliers.find(x => x.name === product.supplier)
    const lead = supplier?.lead_time_days || 3
    const average = (demandHistory[product.sku] || 0) / 90
    const safety = average ? Math.max(1, Math.ceil(average * Math.max(2, lead * .5))) : 0
    const reorderPoint = Math.ceil(average * lead + safety)
    const available = Math.max(0, product.stock_qty)
    const stockoutDays = average ? Math.max(0, Math.floor(available / average)) : null
    const recommended = available <= reorderPoint ? Math.max(product.reorder_qty || 25, Math.ceil(average * (lead + 30) + safety - available)) : 0
    const date = stockoutDays === null ? null : new Date(today.getTime() + stockoutDays * 86400000).toISOString().slice(0, 10)
    const risk = available <= 0 ? 'out' : stockoutDays !== null && stockoutDays <= lead ? 'urgent' : recommended ? 'watch' : 'healthy'
    const plan = demandPlanningState.plans.find(x => x.sku === product.sku)
    return { sku:product.sku, product:product.name, supplier:product.supplier, stock_qty:product.stock_qty, reserved_qty:0, available_qty:available, average_daily_demand:Number(average.toFixed(2)), lead_time_days:lead, safety_stock:safety, reorder_point:reorderPoint, stockout_days:stockoutDays, projected_stockout:date, recommended_qty:recommended, unit_cost:product.cost_price || product.price, estimated_cost:recommended * (product.cost_price || product.price), risk, plan_id:plan?.id || null, plan_status:plan?.status || null, po_no:plan?.po_no || null }
  }).sort((a,b) => ({out:0,urgent:1,watch:2,healthy:3}[a.risk] - ({out:0,urgent:1,watch:2,healthy:3}[b.risk]) || b.recommended_qty - a.recommended_qty))
  const totals = {}
  items.filter(x => x.recommended_qty).forEach(item => { const group = totals[item.supplier] ||= { supplier:item.supplier, recommended_qty:0, estimated_cost:0, sku_count:0 }; group.recommended_qty += item.recommended_qty; group.estimated_cost += item.estimated_cost; group.sku_count += 1 })
  return { window_days:90, horizon_days:30, generated_at:new Date().toISOString(), summary:{ at_risk:items.filter(x => x.recommended_qty).length, stockout_soon:items.filter(x => x.stockout_days !== null && x.stockout_days <= x.lead_time_days).length, estimated_cost:items.reduce((sum,x) => sum + x.estimated_cost, 0), forecasted_skus:items.length }, items, supplier_totals:Object.values(totals) }
}

export const rfqState = {
  items: [{
    id:1, rfq_no:'RFQ-260923-FLT', sku:'FLT-2210', product:'Engine Oil Filter', quantity:60, needed_by:'2026-09-30', status:'quoted', purchase_plan_id:null, notes:'Compare preferred suppliers before replenishing the oil-filter demand plan.', requested_by:'Kabir Store', created_at:'2026-09-23T09:15:00+05:30', recommended_offer_id:1, recommended_supplier:'TorqueLine Components', recommended_score:93.4,
    offers:[
      { id:1, supplier:'TorqueLine Components', supplier_rating:4.8, unit_price:245, total:14700, lead_time_days:3, moq:20, available_qty:100, payment_terms:'Net 30', status:'received', notes:'Standard replenishment quote', score:93.4, is_recommended:true },
      { id:2, supplier:'VoltEdge Electricals', supplier_rating:4.7, unit_price:255, total:15300, lead_time_days:2, moq:25, available_qty:55, payment_terms:'Net 15', status:'received', notes:'Faster delivery, smaller credit window', score:86.1, is_recommended:false },
    ],
  }],
}

export const portalState = { tokens: {} }

export const customers = [
  { id:1, name:'Anil Verma', company:'Metro Garage', email:'anil@metrogarage.demo', phone:'+91 98111 10001', customer_type:'workshop', credit_limit:100000, payment_terms_days:15, outstanding_balance:18450, notes:'Regular brake and service parts buyer.' },
  { id:2, name:'Priya Nair', company:'Northline Repairs', email:'priya@northline.demo', phone:'+91 98111 10002', customer_type:'dealer', credit_limit:250000, payment_terms_days:30, outstanding_balance:32600, notes:'Priority dealer pricing.' },
  { id:3, name:'Imran Sheikh', company:'Rapid Fleet Care', email:'imran@rapidfleet.demo', phone:'+91 98111 10003', customer_type:'fleet', credit_limit:400000, payment_terms_days:30, outstanding_balance:12780, notes:'Fleet maintenance account.' },
]

export const priceRules = [
  { id:1, name:'Dealer 10+ units', customer_type:'dealer', min_qty:10, discount_percent:4, active:true },
  { id:2, name:'Fleet bulk 25+', customer_type:'fleet', min_qty:25, discount_percent:7.5, active:true },
  { id:3, name:'Workshop pack 12+', customer_type:'workshop', min_qty:12, discount_percent:5, active:true },
]

export function analyticsData(){
  const inventoryValue=inventory.reduce((s,p)=>s+p.price*p.stock_qty,0)
  const inventoryCost=inventory.reduce((s,p)=>s+(p.cost_price||0)*p.stock_qty,0)
  const counts={}; inventory.forEach(p=>{counts[p.category]=(counts[p.category]||0)+1})
  const vendor={}; inventory.forEach(p=>{vendor[p.supplier]=(vendor[p.supplier]||0)+1})
  return {
    metrics:{sales_total:salesFlow.orders.reduce((s,o)=>s+o.total,0),invoice_total:salesFlow.invoices.reduce((s,i)=>s+i.total,0),inventory_value:inventoryValue,inventory_cost:inventoryCost,estimated_inventory_margin:Math.max(0,inventoryValue-inventoryCost),outstanding:customers.reduce((s,c)=>s+c.outstanding_balance,0),quote_conversion:quotations.length?Math.round(quotations.filter(q=>q.status==='approved').length/quotations.length*1000)/10:0,low_stock:inventory.filter(p=>p.stock_qty<=p.reorder_level).length},
    operations:{open_purchase_orders:purchaseOrders.filter(x=>!['received','cancelled'].includes(x.status)).length,open_rfqs:rfqState.items.filter(x=>!['selected','closed'].includes(x.status)).length,receiving_exceptions:receivingState.orders.reduce((s,o)=>s+o.invoices.filter(i=>i.status==='exception').length,0),warehouse_units:warehouseState.warehouses.reduce((s,w)=>s+w.units,0),at_risk_suppliers:supplierPerformanceState.suppliers.filter(x=>x.on_time_rate!==null&&x.on_time_rate<95).length},
    alerts:[
      { id:1, severity:'urgent', title:'RLY-24V4 is out of stock', detail:'Demand planning recommends a 90-unit replenishment.' },
      { id:2, severity:'watch', title:'Noida North is at 89% capacity', detail:'Move slow-moving stock before the next inbound receipt.' },
      { id:3, severity:'review', title:'TorqueLine contract expires soon', detail:'Renewal decision required before 15 Oct 2026.' },
      { id:4, severity:'review', title:'Supplier invoice exception', detail:'VE-INV-8821 includes damaged units in its billed quantity.' },
    ],
    categories:Object.entries(counts).map(([label,value])=>({label,value})),suppliers:Object.entries(vendor).map(([label,value])=>({label,value})),top_customers:[...customers].sort((a,b)=>b.outstanding_balance-a.outstanding_balance).map(c=>({label:c.company||c.name,value:c.outstanding_balance})).slice(0,6)
  }
}

export const governanceState = {
  notifications:[
    { id:1, title:'Low stock needs attention', message:'RLY-24V4 is out of stock and has a preferred supplier.', read:false, created_at:'2026-09-21T11:45:00+05:30' },
    { id:2, title:'Purchase order expected tomorrow', message:'PO-260920-90BD is due from VoltEdge Electricals.', read:false, created_at:'2026-09-21T10:30:00+05:30' },
  ],
  approvals:[
    { id:1, kind:'discount', reference:'QT-260921-104 / 9% discount', amount:1650, status:'pending', requested_by:'Rohan Sales', reviewed_by:null, notes:'Fleet follow-up opportunity', created_at:'2026-09-21T11:20:00+05:30' },
  ],
  audits:[
    { id:1, user:'Kabir Store', action:'stock movement', entity:'product', entity_id:'6', detail:'out 18 / INV-5880', created_at:'2026-09-21T09:50:00+05:30' },
    { id:2, user:'Rohan Sales', action:'create', entity:'quotation', entity_id:'1', detail:'QT-260921-104', created_at:'2026-09-21T09:18:00+05:30' },
  ],
}
