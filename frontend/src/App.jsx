import { useState, useRef, useCallback } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

function generateSessionId() {
  return 'sess_' + Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => {
    try {
      const stored = localStorage.getItem('support_session_id')
      if (stored) return stored
    } catch (_) {}
    const id = generateSessionId()
    try {
      localStorage.setItem('support_session_id', id)
    } catch (_) {}
    return id
  })
  const bottomRef = useRef(null)
  const streamedContentRef = useRef('')

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)
    streamedContentRef.current = ''
    setMessages((prev) => [...prev, { role: 'assistant', content: '', streaming: true }])

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      if (!res.ok) {
        const errBody = await res.text()
        let detail = res.statusText
        try {
          const j = JSON.parse(errBody)
          detail = j.detail || j.message || detail
        } catch (_) {}
        throw new Error(detail)
      }
      if (!res.body) {
        throw new Error('No response body')
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let receivedDoneOrError = false
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'text' && data.content) {
                streamedContentRef.current += data.content
                setMessages((prev) => {
                  const next = [...prev]
                  const last = next[next.length - 1]
                  if (last?.role === 'assistant' && last?.streaming) {
                    next[next.length - 1] = {
                      ...last,
                      content: streamedContentRef.current,
                    }
                  }
                  return next
                })
                scrollToBottom()
              } else if (data.type === 'done') {
                receivedDoneOrError = true
                setMessages((prev) => {
                  const next = [...prev]
                  const last = next[next.length - 1]
                  if (last?.role === 'assistant' && last?.streaming) {
                    next[next.length - 1] = { ...last, streaming: false }
                  }
                  return next
                })
              } else if (data.type === 'error') {
                receivedDoneOrError = true
                setMessages((prev) => {
                  const next = [...prev]
                  const last = next[next.length - 1]
                  if (last?.role === 'assistant' && last?.streaming) {
                    next[next.length - 1] = { ...last, content: data.content || 'Something went wrong.', streaming: false }
                  } else {
                    next.push({ role: 'assistant', content: data.content || 'Something went wrong.', streaming: false })
                  }
                  return next
                })
              }
            } catch (_) {}
          }
        }
      }
      if (!receivedDoneOrError) {
        setMessages((prev) => {
          const next = prev.filter((m) => !(m.role === 'assistant' && m.streaming))
          return [...next, { role: 'assistant', content: 'Connection ended unexpectedly. Please try again.', streaming: false }]
        })
      }
    } catch (e) {
      setMessages((prev) => {
        const next = prev.filter((m) => !(m.role === 'assistant' && m.streaming))
        return [...next, { role: 'assistant', content: `Error: ${e.message}`, streaming: false }]
      })
    } finally {
      setLoading(false)
      scrollToBottom()
    }
  }

  return (
    <div className="chat-widget">
      <header className="chat-header">
        <span className="chat-title">ShopRight Support</span>
        <span className="chat-subtitle">Ask about orders & policies</span>
      </header>
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome welcome-enter">
            <p>Hi! Ask me about returns, shipping, warranty, or order status.</p>
            <p className="hint">Try: &quot;Where is order #123?&quot; or &quot;What is your return policy?&quot;</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message message-${m.role} message-enter`}>
            <span className="message-role">{m.role === 'user' ? 'You' : 'Support'}</span>
            <div className="message-content">
              {m.content ? (
                m.content
              ) : m.streaming ? (
                <span className="typing-indicator">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </span>
              ) : null}
              {m.streaming && m.content && <span className="caret" />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form
        className="input-row"
        onSubmit={(e) => {
          e.preventDefault()
          sendMessage()
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question..."
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
