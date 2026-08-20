import '@/styles/globals.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './shared/context/AuthContext'
import AppRouter from './app/Router'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </StrictMode>
)
