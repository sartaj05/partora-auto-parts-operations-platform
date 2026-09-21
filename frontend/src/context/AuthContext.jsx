import { createContext, useContext, useMemo, useState } from 'react'
import { login as apiLogin } from '../api/client'

const AuthContext = createContext(null)
const STORAGE = 'partora_session'

function readSession() {
  try { return JSON.parse(localStorage.getItem(STORAGE)) || null } catch { return null }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession)

  async function login(email, password) {
    const result = await apiLogin(email, password)
    const next = { user: result.user, modules: result.modules, token: result.token, demoMode: result.demoMode }
    localStorage.setItem(STORAGE, JSON.stringify(next))
    localStorage.setItem('partora_token', result.token)
    setSession(next)
    return result
  }

  function logout() {
    localStorage.removeItem(STORAGE)
    localStorage.removeItem('partora_token')
    setSession(null)
  }

  const value = useMemo(() => ({
    user: session?.user || null,
    modules: session?.modules || [],
    demoMode: session?.demoMode || false,
    login,
    logout,
  }), [session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() { return useContext(AuthContext) }
