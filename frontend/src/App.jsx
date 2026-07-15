import React, { useState, useEffect } from 'react'
import Terminal from './components/Terminal'
import MemorySidebar from './components/MemorySidebar'
import './App.css'

const DEMO_TEAM_ID = 'demo-team-001'

function App() {
  const [tabs, setTabs] = useState([])
  const [activeTabIndex, setActiveTabIndex] = useState(0)
  const [memories, setMemories] = useState([])
  const [qaEntries, setQAEntries] = useState([])
  const [nextTabId, setNextTabId] = useState(1)

  // Initialize with first tab
  useEffect(() => {
    createNewTab()
  }, [])

  // Load recent Q&A
  useEffect(() => {
    loadRecentQA()
  }, [])

  const createNewTab = async () => {
    const tabId = nextTabId
    const tabNumber = tabs.length + 1

    try {
      // Create a new engineer for this tab
      const res = await fetch('/api/engineers/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `Engineer ${tabNumber}`,
          email: `engineer${tabId}@teamagent.demo`,
          git_username: `engineer${tabId}`
        })
      })
      const engineer = await res.json()

      // Create WebSocket for this engineer (use current host for remote access)
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = window.location.hostname
      const wsPort = '8000'
      const wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws/${engineer.id}`
      const socket = new WebSocket(wsUrl)

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data)
        handleWebSocketMessage(message, tabId)
      }

      // Add new tab
      const newTab = {
        id: tabId,
        name: `Terminal ${tabNumber}`,
        engineer,
        ws: socket,
        color: getTabColor(tabNumber)
      }

      setTabs(prev => [...prev, newTab])
      setActiveTabIndex(tabs.length) // Switch to new tab
      setNextTabId(tabId + 1)

      // Load Q&A when first tab is created
      if (tabs.length === 0) {
        loadRecentQA()
      }
    } catch (error) {
      console.error('Failed to create tab:', error)
    }
  }

  const closeTab = (index) => {
    if (tabs.length === 1) {
      alert('Cannot close the last tab!')
      return
    }

    // Close WebSocket
    if (tabs[index].ws) {
      tabs[index].ws.close()
    }

    // Remove tab
    const newTabs = tabs.filter((_, i) => i !== index)
    setTabs(newTabs)

    // Adjust active tab if needed
    if (activeTabIndex >= newTabs.length) {
      setActiveTabIndex(newTabs.length - 1)
    } else if (activeTabIndex > index) {
      setActiveTabIndex(activeTabIndex - 1)
    }
  }

  const getTabColor = (tabNumber) => {
    const colors = [
      '#00ff41', // Green
      '#00d4ff', // Cyan
      '#ff00ff', // Magenta
      '#ffaa00', // Orange
      '#00ffaa', // Teal
      '#ff5555', // Red
      '#ffff00', // Yellow
      '#aa00ff', // Purple
    ]
    return colors[(tabNumber - 1) % colors.length]
  }

  const handleWebSocketMessage = (message, tabId) => {
    if (message.type === 'new_question' || message.type === 'new_answer') {
      loadRecentQA()
      addMemoryEntry({
        type: message.type,
        tabId,
        data: message.data,
        timestamp: new Date()
      })
    }
  }

  const loadRecentQA = async () => {
    try {
      const res = await fetch(`/api/qa/recent?team_id=${DEMO_TEAM_ID}&limit=20`)
      const data = await res.json()
      setQAEntries(data.results || [])
    } catch (error) {
      console.error('Failed to load Q&A:', error)
    }
  }

  const addMemoryEntry = (entry) => {
    setMemories(prev => [entry, ...prev].slice(0, 50))
  }

  const executeCommand = async (command, engineerId, tabName) => {
    try {
      const res = await fetch('/api/command/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command,
          engineer_id: engineerId,
          team_id: DEMO_TEAM_ID
        })
      })
      const result = await res.json()

      // Add to memory visualization
      addMemoryEntry({
        type: 'command',
        engineer: tabName,
        command,
        result: result.output,
        timestamp: new Date()
      })

      return result.output || 'Command executed'
    } catch (error) {
      return `Error: ${error.message}`
    }
  }

  const activeTab = tabs[activeTabIndex]

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🤖 TeamAgent - Collaborative AI Terminal</h1>
        <p>Real-time memory synchronization across engineers</p>
      </header>

      <div className="main-content">
        <div className="terminals-container">
          {/* Tab Bar */}
          <div className="tab-bar">
            {tabs.map((tab, index) => (
              <div
                key={tab.id}
                className={`tab ${index === activeTabIndex ? 'active' : ''}`}
                onClick={() => setActiveTabIndex(index)}
                style={{
                  borderBottomColor: index === activeTabIndex ? tab.color : 'transparent'
                }}
              >
                <span className="tab-name">{tab.name}</span>
                {tabs.length > 1 && (
                  <button
                    className="tab-close"
                    onClick={(e) => {
                      e.stopPropagation()
                      closeTab(index)
                    }}
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <button className="new-tab-btn" onClick={createNewTab}>
              + New Terminal
            </button>
          </div>

          {/* All Terminals (rendered but hidden when not active) */}
          <div className="terminal-content">
            {tabs.map((tab, index) => (
              <div
                key={tab.id}
                className="terminal-instance"
                style={{
                  display: index === activeTabIndex ? 'flex' : 'none',
                  flex: 1,
                  flexDirection: 'column'
                }}
              >
                <Terminal
                  engineerId={tab.engineer.id}
                  engineerName={tab.name}
                  teamId={DEMO_TEAM_ID}
                  onCommand={(cmd) => executeCommand(cmd, tab.engineer.id, tab.name)}
                  color={tab.color}
                />
              </div>
            ))}
          </div>
        </div>

        <MemorySidebar
          memories={memories}
          qaEntries={qaEntries}
        />
      </div>

      <footer className="app-footer">
        <div className="demo-instructions">
          <strong>Try it:</strong>
          <code>log variable x = 5</code> in one terminal, then
          <code>ai what is variable x?</code> in another tab to see the hive mind in action
        </div>
      </footer>
    </div>
  )
}

export default App
