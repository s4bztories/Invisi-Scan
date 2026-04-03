import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

function reportClientError(payload) {
  fetch(`${API_BASE_URL}/api/observability/client-error`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch(() => {
    // Best-effort telemetry; never block app boot.
  })
}

window.addEventListener('error', (event) => {
  reportClientError({
    message: event.message || 'Unknown client error',
    stack: event.error?.stack || null,
    path: window.location.pathname,
    source: 'window.error',
  })
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  reportClientError({
    message: typeof reason === 'string' ? reason : (reason?.message || 'Unhandled promise rejection'),
    stack: reason?.stack || null,
    path: window.location.pathname,
    source: 'window.unhandledrejection',
  })
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
