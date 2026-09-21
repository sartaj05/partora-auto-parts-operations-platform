export const demoAccounts = [
  { email: 'admin@partora.demo', password: 'demo123', name: 'Aarav Admin', role: 'admin' },
  { email: 'manager@partora.demo', password: 'demo123', name: 'Meera Manager', role: 'manager' },
  { email: 'sales@partora.demo', password: 'demo123', name: 'Rohan Sales', role: 'sales' },
  { email: 'store@partora.demo', password: 'demo123', name: 'Kabir Store', role: 'store' },
]

export const modulesByRole = {
  admin: ['dashboard', 'inventory', 'quotations', 'suppliers', 'stock', 'barcodes', 'fitments', 'purchase_orders', 'warehouses', 'reorder'],
  manager: ['dashboard', 'inventory', 'quotations', 'suppliers', 'stock', 'barcodes', 'fitments', 'purchase_orders', 'warehouses', 'reorder'],
  sales: ['dashboard', 'inventory', 'quotations', 'barcodes', 'fitments'],
  store: ['dashboard', 'inventory', 'stock', 'barcodes', 'fitments', 'purchase_orders', 'warehouses', 'reorder'],
}

export const inventory = [
  { id: 1, sku: 'BRK-1048', name: 'Ceramic Brake Pad Set', brand: 'RoadShield', category: 'auto', supplier: 'TorqueLine Components', price: 2450, stock_qty: 38, reorder_level: 12, reorder_qty: 30, stock_status: 'healthy', bin_location: 'A-04-12', barcode: '890100010481' },
  { id: 2, sku: 'FLT-2210', name: 'Engine Oil Filter', brand: 'MotoPure', category: 'auto', supplier: 'TorqueLine Components', price: 420, stock_qty: 8, reorder_level: 15, reorder_qty: 40, stock_status: 'low', bin_location: 'A-02-03', barcode: '890100022102' },
  { id: 3, sku: 'BLT-0812', name: 'Hex Bolt M8 × 20 mm', brand: 'ForgeFast', category: 'hardware', supplier: 'ForgeFast Hardware', price: 12, stock_qty: 640, reorder_level: 120, reorder_qty: 250, stock_status: 'healthy', bin_location: 'H-11-08', barcode: '890100008123' },
  { id: 4, sku: 'BRG-6204', name: 'Deep Groove Bearing 6204', brand: 'AxisPro', category: 'hardware', supplier: 'ForgeFast Hardware', price: 310, stock_qty: 5, reorder_level: 18, reorder_qty: 50, stock_status: 'low', bin_location: 'H-03-14', barcode: '890100062043' },
  { id: 5, sku: 'MCB-C32', name: '32A C-Curve MCB', brand: 'VoltEdge', category: 'electrical', supplier: 'VoltEdge Electricals', price: 690, stock_qty: 72, reorder_level: 20, reorder_qty: 50, stock_status: 'healthy', bin_location: 'E-08-02', barcode: '890100032003' },
  { id: 6, sku: 'RLY-24V4', name: '24V 4-Pin Automotive Relay', brand: 'VoltEdge', category: 'electrical', supplier: 'VoltEdge Electricals', price: 180, stock_qty: 0, reorder_level: 16, reorder_qty: 40, stock_status: 'out', bin_location: 'E-05-09', barcode: '890100024004' },
  { id: 7, sku: 'HLM-H7', name: 'H7 LED Headlamp Pair', brand: 'NightArc', category: 'auto', supplier: 'VoltEdge Electricals', price: 1650, stock_qty: 26, reorder_level: 10, reorder_qty: 25, stock_status: 'healthy', bin_location: 'A-09-01', barcode: '890100000707' },
  { id: 8, sku: 'CBL-25R', name: '2.5 sq mm Copper Cable Roll', brand: 'VoltEdge', category: 'electrical', supplier: 'VoltEdge Electricals', price: 3250, stock_qty: 14, reorder_level: 8, reorder_qty: 20, stock_status: 'healthy', bin_location: 'E-12-04', barcode: '890100025007' },
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

export const purchaseOrders = [
  { id:1, po_no:'PO-260921-A12F', supplier:'TorqueLine Components', status:'ordered', expected_date:'2026-09-24', total:25200, created_by:'Meera Manager', line_count:3, received_lines:0 },
  { id:2, po_no:'PO-260920-90BD', supplier:'VoltEdge Electricals', status:'partial', expected_date:'2026-09-23', total:44100, created_by:'Aarav Admin', line_count:4, received_lines:2 },
]

export const warehouseState = {
  warehouses: [
    { id:1, code:'DEL-MAIN', name:'Delhi Main Warehouse', address:'Okhla Industrial Area, Delhi', sku_count:8, units:781 },
    { id:2, code:'GUR-SAT', name:'Gurugram Satellite Store', address:'Udyog Vihar, Gurugram', sku_count:5, units:214 },
    { id:3, code:'NOI-NTH', name:'Noida North Store', address:'Sector 63, Noida', sku_count:4, units:133 },
  ],
  transfers: [
    { id:1, reference:'TR-260921-2A7F', from_warehouse:'DEL-MAIN', to_warehouse:'GUR-SAT', sku:'BRK-1048', product:'Ceramic Brake Pad Set', quantity:12, status:'completed', created_at:'2026-09-21T10:25:00+05:30' },
  ],
}

export function reorderSuggestions(){
  return inventory.filter(p=>p.stock_qty<=p.reorder_level).map(p=>({id:p.id,sku:p.sku,name:p.name,supplier:p.supplier,stock_qty:p.stock_qty,reorder_level:p.reorder_level,suggested_qty:Math.max(p.reorder_qty||25,p.reorder_level*2-p.stock_qty),unit_price:p.price,severity:p.stock_qty<=0?'out':'low'}))
}
