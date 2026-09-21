import { demoAccounts, fitments, inventory, mockDashboard, modulesByRole, purchaseOrders, quotations, stock, suppliers, warehouseState } from '../mock/data'

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
  '/warehouses/': () => warehouseState,
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

function createMock(path, payload, role) {
  const id = Date.now()
  if (path === '/warehouses/') {
    if(payload.action==='warehouse'){const item={id:Date.now(),code:String(payload.code||'').toUpperCase(),name:payload.name,address:payload.address||'',sku_count:0,units:0};warehouseState.warehouses.push(item);return {item}}
    const item={id:Date.now(),reference:`TR-DEMO-${String(Date.now()).slice(-4)}`,from_warehouse:String(payload.from_warehouse||'').toUpperCase(),to_warehouse:String(payload.to_warehouse||'').toUpperCase(),sku:String(payload.sku||'').toUpperCase(),product:inventory.find(x=>x.sku===String(payload.sku||'').toUpperCase())?.name||'Demo part',quantity:Number(payload.quantity||1),status:'completed',created_at:new Date().toISOString()};warehouseState.transfers.unshift(item);return {item}
  }
  if (path === '/purchase-orders/') {
    if(payload.action==='receive'){const po=purchaseOrders.find(x=>x.id===Number(payload.id));if(!po)throw new Error('PO not found');po.status='received';po.received_lines=po.line_count;return {item:po}}
    const product=inventory.find(x=>x.sku.toUpperCase()===String(payload.sku||'').toUpperCase());if(!product)throw new Error('SKU not found')
    const item={id:Date.now(),po_no:`PO-DEMO-${String(Date.now()).slice(-4)}`,supplier:payload.supplier,status:payload.status||'draft',expected_date:payload.expected_date||null,total:Number(payload.quantity||1)*Number(payload.unit_cost||product.price),created_by:'Demo User',line_count:1,received_lines:0};purchaseOrders.unshift(item);return {item}
  }
  if (path === '/fitments/') {
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
