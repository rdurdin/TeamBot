import React, { useState } from 'react'
import './MemorySidebar.css'

function MemorySidebar({ memories, qaEntries }) {
  const [activeTab, setActiveTab] = useState('live')

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getEngineerColor = (engineer) => {
    return engineer === 'A' ? '#00ff41' : '#00d4ff'
  }

  const renderLiveMemory = () => {
    if (memories.length === 0) {
      return (
        <div className="empty-state">
          <p>No activity yet</p>
          <p className="empty-hint">Commands from terminals will appear here in real-time</p>
        </div>
      )
    }

    return (
      <div className="memory-list">
        {memories.map((mem, idx) => (
          <div key={idx} className="memory-item">
            <div className="memory-header">
              <span
                className="engineer-badge"
                style={{ backgroundColor: getEngineerColor(mem.engineer) }}
              >
                {mem.engineer}
              </span>
              <span className="memory-time">{formatTimestamp(mem.timestamp)}</span>
            </div>

            {mem.type === 'command' && (
              <div className="memory-content">
                <div className="memory-command">
                  <span className="prompt">$</span> {mem.command}
                </div>
                <div className="memory-result">
                  {mem.result && mem.result.substring(0, 150)}
                  {mem.result && mem.result.length > 150 && '...'}
                </div>
              </div>
            )}

            {mem.type === 'new_question' && (
              <div className="memory-content event-question">
                <div className="event-label">❓ New Question</div>
                <div className="event-text">{mem.data.question}</div>
              </div>
            )}

            {mem.type === 'new_answer' && (
              <div className="memory-content event-answer">
                <div className="event-label">✓ Answer Added</div>
                <div className="event-text">{mem.data.answer?.substring(0, 100)}</div>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderQAArchive = () => {
    if (qaEntries.length === 0) {
      return (
        <div className="empty-state">
          <p>No Q&A entries yet</p>
          <p className="empty-hint">Use 'ask' command to create questions</p>
        </div>
      )
    }

    return (
      <div className="qa-list">
        {qaEntries.map((qa) => (
          <div key={qa.id} className={`qa-item ${qa.status}`}>
            <div className="qa-status">
              {qa.status === 'answered' ? '✓' : '?'}
            </div>
            <div className="qa-content">
              <div className="qa-question">{qa.question}</div>
              {qa.answer && (
                <div className="qa-answer">
                  <strong>A:</strong> {qa.answer}
                </div>
              )}
              <div className="qa-meta">
                {formatTimestamp(qa.asked_at)}
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="memory-sidebar">
      <div className="sidebar-header">
        <h2>🧠 Team Memory</h2>
        <div className="memory-stats">
          <div className="stat">
            <span className="stat-value">{memories.length}</span>
            <span className="stat-label">Live Events</span>
          </div>
          <div className="stat">
            <span className="stat-value">{qaEntries.length}</span>
            <span className="stat-label">Q&A Archive</span>
          </div>
        </div>
      </div>

      <div className="sidebar-tabs">
        <button
          className={`tab ${activeTab === 'live' ? 'active' : ''}`}
          onClick={() => setActiveTab('live')}
        >
          Live Feed
        </button>
        <button
          className={`tab ${activeTab === 'archive' ? 'active' : ''}`}
          onClick={() => setActiveTab('archive')}
        >
          Q&A Archive
        </button>
      </div>

      <div className="sidebar-content">
        {activeTab === 'live' ? renderLiveMemory() : renderQAArchive()}
      </div>
    </div>
  )
}

export default MemorySidebar
