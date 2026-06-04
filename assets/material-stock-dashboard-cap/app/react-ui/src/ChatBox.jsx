import { useState, useRef, useEffect, useCallback } from 'react'
import { Button, BusyIndicator, Input, MessageStrip, Title, Tag } from '@ui5/webcomponents-react'
import '@ui5/webcomponents-icons/dist/paper-plane.js'
import '@ui5/webcomponents-icons/dist/refresh.js'
import './ChatBox.css'

const SUGGESTED_QUESTIONS = [
  'What should I reorder today?',
  'Show me the most critical items',
  'Give me a stock summary',
  'What are the at-risk items in plant 1000?',
]

/** Render markdown-style bold (**text**) in message content */
function renderMarkdown(text) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    const parts = line.split(/\*\*(.*?)\*\*/g)
    return (
      <span key={i}>
        {parts.map((part, j) =>
          j % 2 === 1 ? <strong key={j}>{part}</strong> : part
        )}
        {i < text.split('\n').length - 1 && <br />}
      </span>
    )
  })
}

export default function ChatBox() {
  const [messages, setMessages]   = useState([
    { role: 'agent', text: '👋 Hi! I\'m your **Stock Advisor**. Ask me anything about your inventory — like which materials to reorder, critical items by plant, or a stock health summary.' }
  ])
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [contextId]               = useState(`chat-${Date.now()}`)
  const messagesEndRef             = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return

    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setLoading(true)

    try {
      const res = await fetch('/stock/chat', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ message: msg, contextId }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      const data = await res.json()
      // CAP action response: { value: "..." }
      const reply = data?.value || data?.result || 'No response received.'
      setMessages(prev => [...prev, { role: 'agent', text: reply }])
    } catch (e) {
      setError(e.message)
      setMessages(prev => [...prev, { role: 'agent', text: `⚠️ Sorry, I encountered an error: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, contextId])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([{ role: 'agent', text: '👋 Chat cleared. How can I help you with your inventory?' }])
    setError(null)
  }

  return (
    <div className="chatbox-container">
      {/* Header */}
      <div className="chatbox-header">
        <span className="chatbox-header-icon">🤖</span>
        <Title level="H5" style={{ margin: 0, color: 'var(--sapBaseColor, #fff)' }}>
          Stock Advisor
        </Title>
        <Button
          design="Transparent"
          icon="refresh"
          tooltip="Clear chat"
          onClick={clearChat}
          style={{ marginLeft: 'auto', color: 'var(--sapBaseColor, #fff)' }}
        />
      </div>

      {/* Suggested questions (only at start) */}
      {messages.length === 1 && (
        <div className="chatbox-suggestions">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button key={q} className="suggestion-chip" onClick={() => sendMessage(q)}>
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="chatbox-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-message chat-message--${m.role}`}>
            {m.role === 'agent' && (
              <div className="chat-avatar">🤖</div>
            )}
            <div className="chat-bubble">
              {renderMarkdown(m.text)}
            </div>
            {m.role === 'user' && (
              <div className="chat-avatar chat-avatar--user">👤</div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-message chat-message--agent">
            <div className="chat-avatar">🤖</div>
            <div className="chat-bubble chat-bubble--typing">
              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <MessageStrip design="Negative" onClose={() => setError(null)} style={{ margin: '0.25rem 0.5rem' }}>
          {error}
        </MessageStrip>
      )}

      {/* Input */}
      <div className="chatbox-input-row">
        <Input
          placeholder="Ask a question about your stock…"
          value={input}
          onInput={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          style={{ flex: 1 }}
        />
        <Button
          design="Emphasized"
          icon="paper-plane"
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          tooltip="Send message"
        />
      </div>
    </div>
  )
}
