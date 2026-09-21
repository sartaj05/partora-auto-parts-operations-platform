import { demoAccounts, inventory, mockDashboard, modulesByRole, quotations, stock, suppliers } from '../mock/data'

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
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw Object.assign(new Error(body.detail || 'Request failed'), { status: response.status })
  return body
}

export async function login(email, password) {
  try {
    const result = await request('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) })
    return { ...result, demoMode: false }
  } catch (error) {
    if (error.status) throw error
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
