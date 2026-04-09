import { useState, useEffect, useRef, useCallback } from 'react'

const API_URL = 'http://localhost:8000'

// ── Session ID persisted across refreshes ────────────────────────────────────
const getSessionId = () => {
  let id = localStorage.getItem('lifeops_session_id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('lifeops_session_id', id)
  }
  return id
}

const nowStr = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const TOOL_LABELS = {
  get_calendar_events: '🔍 Checking your calendar…',
  create_event:        '📅 Creating calendar event…',
}

function ConnectScreen({ onConnected, authError }) {
  return (
    <div className="connect-screen">
      <div className="connect-card">
        {/* Logo */}
        <div className="connect-logo">⚡</div>
        <h1 className="connect-title">Life-Ops</h1>
        <p className="connect-subtitle">Your AI-powered scheduling assistant</p>

        {/* Error banner */}
        {authError && (
          <div className="connect-error">
            ⚠️ Authentication failed: {authError}. Please try again.
          </div>
        )}

        {/* Features */}
        <div className="connect-features">
          <div className="connect-feature">
            <span>📅</span>
            <div>
              <strong>Read your calendar</strong>
              <p>Ask about your schedule in plain English</p>
            </div>
          </div>
          <div className="connect-feature">
            <span>✨</span>
            <div>
              <strong>Create events instantly</strong>
              <p>Just say "schedule gym Friday at 5pm"</p>
            </div>
          </div>
          <div className="connect-feature">
            <span>🤖</span>
            <div>
              <strong>AI-powered reasoning</strong>
              <p>Understands context, relative dates, and conflicts</p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <a
          id="connect-google-btn"
          className="connect-btn"
          href={`${API_URL}/auth/login`}
        >
          <svg className="google-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Connect Google Calendar
        </a>

        <p className="connect-disclaimer">
          Life-Ops only accesses your calendar — no email, contacts, or other data.
        </p>
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="message-wrapper agent">
      <div className="avatar agent-avatar">⚡</div>
      <div className="bubble agent-bubble typing">
        <span /><span /><span />
      </div>
    </div>
  )
}

function MessageBubble({ msg }) {
  if (msg.role === 'system') {
    return (
      <div className="system-pill">
        <span className="tool-icon">🔧</span>
        {msg.content}
      </div>
    )
  }

  const isUser  = msg.role === 'user'
  const isError = msg.isError

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'agent'}`}>
      {!isUser && <div className="avatar agent-avatar">⚡</div>}
      <div className={`bubble ${isUser ? 'user-bubble' : 'agent-bubble'} ${isError ? 'error-bubble' : ''}`}>
        <p>{msg.content}</p>
        {msg.time && <span className="timestamp">{msg.time}</span>}
      </div>
      {isUser && <div className="avatar user-avatar">👤</div>}
    </div>
  )
}

export default function App() {
  const [auth, setAuth]     = useState(null)
  const [authError, setAuthError] = useState(null)
  const [messages, setMessages]   = useState([
    {
      role: 'agent',
      content: "Hey! I'm Life-Ops, your AI scheduling assistant.\nI'm connected to your Google Calendar — ask me anything:\n• \"What's on my calendar this week?\"\n• \"Schedule a gym session Friday at 5 PM\"\n• \"Am I free tomorrow afternoon?\"",
      time: nowStr(),
    },
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)

  const bottomRef = useRef(null)
  const inputRef  = useRef(null)
  const sessionId = useRef(getSessionId())

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)

    if (params.get('auth_success')) {
      window.history.replaceState({}, '', '/')
    }
    if (params.get('auth_error')) {
      setAuthError(decodeURIComponent(params.get('auth_error')))
      window.history.replaceState({}, '', '/')
    }

    fetch(`${API_URL}/auth/status`)
      .then(r => r.json())
      .then(data => setAuth(data.authenticated))
      .catch(() => setAuth(false))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const addMessages = useCallback((msgs) => {
    setMessages(prev => [...prev, ...msgs])
  }, [])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return

    const userMsg = { role: 'user', content: input.trim(), time: nowStr() }
    addMessages([userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, thread_id: sessionId.current }),
      })

      if (res.status === 401) {
        setAuth(false)  
        return
      }
      if (!res.ok) throw new Error(`Server responded with ${res.status}`)

      const data    = await res.json()
      const newMsgs = []

      if (data.tool_calls?.length) {
        data.tool_calls.forEach(tool => {
          newMsgs.push({ role: 'system', content: TOOL_LABELS[tool] ?? `⚙️ Calling ${tool}…` })
        })
      }
      newMsgs.push({ role: 'agent', content: data.response || '(No response)', time: nowStr() })
      addMessages(newMsgs)
    } catch (err) {
      addMessages([{
        role: 'agent',
        content: `⚠️ ${err.message}.\n\nMake sure the backend is running:\n  cd backend && uvicorn main:app --reload`,
        time: nowStr(),
        isError: true,
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [input, loading, addMessages])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  const handleDisconnect = async () => {
    await fetch(`${API_URL}/auth/disconnect`)
    setAuth(false)
    setMessages([])
  }

  if (auth === null) {
    return (
      <div className="app loading-screen">
        <div className="loading-logo">⚡</div>
        <p>Starting Life-Ops…</p>
      </div>
    )
  }

  if (!auth) {
    return <ConnectScreen authError={authError} />
  }

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-brand">
          <div className="logo">⚡</div>
          <div>
            <h1>Life-Ops</h1>
            <p>AI Scheduling Assistant</p>
          </div>
        </div>
        <div className="header-actions">
          <div className="header-status">
            <span className="status-dot" />
            <span>Calendar Connected</span>
          </div>
          <button id="disconnect-btn" className="disconnect-btn" onClick={handleDisconnect} title="Disconnect Google Calendar">
            Disconnect
          </button>
        </div>
      </header>

      {/* ── Chat Window ── */}
      <div className="chat-window" role="log" aria-live="polite">
        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* ── Input Bar ── */}
      <div className="input-bar">
        <textarea
          id="chat-input"
          ref={inputRef}
          className="input-field"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your schedule or create an event…"
          rows={1}
          disabled={loading}
          aria-label="Chat message input"
        />
        <button
          id="send-btn"
          className="send-btn"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          aria-label="Send message"
          title="Send (Enter)"
        >
          {loading ? '…' : '↑'}
        </button>
      </div>
    </div>
  )
}
