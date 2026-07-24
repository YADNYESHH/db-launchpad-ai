import { useEffect, useRef, useState } from 'react'
import { ApiError, askAboutStartup, getChatHistory } from '../api'
import type { ChatMessage } from '../types'
import './ChatPanel.css'

export default function ChatPanel({ startupId }: { startupId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const threadEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    setMessages([])
    setError(null)
    setLoadingHistory(true)
    getChatHistory(startupId)
      .then(setMessages)
      .catch(() => setError('Could not load the conversation history.'))
      .finally(() => setLoadingHistory(false))
  }, [startupId])

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages, asking])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || asking) return

    // Optimistic RM message — the POST endpoint only returns the assistant's reply.
    const optimisticRm: ChatMessage = {
      message_id: `pending-${Date.now()}`,
      startup_id: startupId,
      role: 'rm',
      text: trimmed,
      citations: [],
      llm_used: false,
      guardrail_flags: [],
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticRm])
    setQuestion('')
    setAsking(true)
    setError(null)

    try {
      const reply = await askAboutStartup(startupId, trimmed)
      setMessages((prev) => [...prev, reply])
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Could not reach the assistant. Please try again.')
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-thread">
        {loadingHistory && <p className="chat-empty">Loading conversation…</p>}
        {!loadingHistory && messages.length === 0 && (
          <p className="chat-empty">No questions asked yet. Ask something about this startup below.</p>
        )}
        {messages.map((m) => (
          <ChatBubble key={m.message_id} message={m} />
        ))}
        {asking && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-bubble chat-bubble-thinking" role="status">
              <span className="chat-typing-dot" aria-hidden="true" />
              <span className="chat-typing-dot" aria-hidden="true" />
              <span className="chat-typing-dot" aria-hidden="true" />
              <span className="chat-thinking-label">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={threadEndRef} />
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this startup…"
          disabled={asking}
          aria-label="Ask a question about this startup"
        />
        <button className="chat-send-btn" type="submit" disabled={asking || !question.trim()}>
          {asking ? 'Asking…' : 'Ask'}
        </button>
      </form>
      <p className="chat-note">
        Answers use existing records first; may attempt a live lookup for anything not on file.
      </p>
    </div>
  )
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isRm = message.role === 'rm'
  return (
    <div className={`chat-msg ${isRm ? 'chat-msg-rm' : 'chat-msg-assistant'}`}>
      <div className="chat-bubble">
        <p className="chat-text">{message.text}</p>
        {!isRm && (
          <div className="chat-meta">
            <span className={`chat-badge ${message.llm_used ? 'chat-badge-live' : 'chat-badge-file'}`}>
              {message.llm_used ? 'Live-verified' : 'From records'}
            </span>
            {message.guardrail_flags.length > 0 && (
              <span className="guardrail-warning chat-guardrail">
                guardrail flags: {message.guardrail_flags.join(', ')}
              </span>
            )}
          </div>
        )}
        {!isRm && message.citations.length > 0 && (
          <ul className="chat-citations">
            {message.citations.map((c, i) => (
              <li key={i}>
                <a href={c} target="_blank" rel="noreferrer">
                  {c}
                </a>
              </li>
            ))}
          </ul>
        )}
        <span className="chat-timestamp">{new Date(message.created_at).toLocaleString()}</span>
      </div>
    </div>
  )
}
