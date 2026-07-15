import React, { useEffect, useRef, useState } from 'react'
import { Terminal as XTerm } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import './Terminal.css'

const WELCOME_LINES = [
  '',
  '\x1b[1;36m  TeamAgent Collaborative Terminal\x1b[0m',
  '\x1b[90m  ---------------------------------\x1b[0m',
  '',
  '\x1b[37m  Commands:\x1b[0m',
  '\x1b[32m    ask \x1b[90m<question>\x1b[0m      Ask a question',
  '\x1b[32m    ai \x1b[90m<question>\x1b[0m       Get an AI response',
  '\x1b[32m    search \x1b[90m<query>\x1b[0m      Search team knowledge',
  '\x1b[32m    log \x1b[90m<info>\x1b[0m          Save to team memory',
  '\x1b[32m    recent\x1b[0m               View recent Q&A',
  '\x1b[32m    memory\x1b[0m               View memory entries',
  '\x1b[32m    help\x1b[0m                 Show all commands',
  '',
]

function Terminal({ engineerId, engineerName, teamId, onCommand, color }) {
  const terminalRef = useRef(null)
  const xtermRef = useRef(null)
  const fitAddonRef = useRef(null)
  const [commandBuffer, setCommandBuffer] = useState('')
  const [commandHistory, setCommandHistory] = useState([])
  const [historyIndex, setHistoryIndex] = useState(-1)

  useEffect(() => {
    if (!terminalRef.current) return

    // Initialize xterm
    const term = new XTerm({
      cursorBlink: true,
      cursorStyle: 'block',
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: 16, // Increased for better readability
      lineHeight: 1.4, // Better line spacing
      theme: {
        background: '#0a0e27',
        foreground: color,
        cursor: color,
        selection: 'rgba(255, 255, 255, 0.3)',
        black: '#0a0e27',
        red: '#ff5555',
        green: '#00ff41',
        yellow: '#ffb86c',
        blue: '#00d4ff',
        magenta: '#ff79c6',
        cyan: '#8be9fd',
        white: '#f8f8f2'
      },
      allowProposedApi: true
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)

    term.open(terminalRef.current)
    fitAddon.fit()

    xtermRef.current = term
    fitAddonRef.current = fitAddon

    // Welcome message
    WELCOME_LINES.forEach(line => term.writeln(line))
    writePrompt()

    // Handle input
    let currentLine = ''

    term.onData((data) => {
      const code = data.charCodeAt(0)

      if (code === 13) { // Enter
        term.writeln('')
        if (currentLine.trim()) {
          handleCommand(currentLine.trim())
          setCommandHistory(prev => [...prev, currentLine.trim()])
        }
        currentLine = ''
        setCommandBuffer('')
      } else if (code === 127) { // Backspace
        if (currentLine.length > 0) {
          currentLine = currentLine.slice(0, -1)
          term.write('\b \b')
          setCommandBuffer(currentLine)
        }
      } else if (code === 27) { // Escape sequences (arrow keys, etc.)
        // Handle arrow keys for history navigation
        return
      } else if (code >= 32 && code <= 126) { // Printable characters
        currentLine += data
        term.write(data)
        setCommandBuffer(currentLine)
      }
    })

    // Resize handler
    const handleResize = () => {
      fitAddon.fit()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      term.dispose()
    }
  }, [])

  const writePrompt = () => {
    if (xtermRef.current) {
      xtermRef.current.write(`\r\n\x1b[1;32m${engineerName}>\x1b[0m `)
    }
  }

  const handleCommand = async (command) => {
    if (!command) return

    const term = xtermRef.current
    if (!term) return

    // Handle built-in commands
    if (command === 'help') {
      term.writeln('')
      term.writeln('\x1b[1;37m  Commands:\x1b[0m')
      term.writeln('\x1b[32m    ask \x1b[90m<question>\x1b[0m      Ask a question to the team')
      term.writeln('\x1b[32m    ai \x1b[90m<question>\x1b[0m       Get an AI response')
      term.writeln('\x1b[32m    search \x1b[90m<query>\x1b[0m      Search team knowledge')
      term.writeln('\x1b[32m    log \x1b[90m<info>\x1b[0m          Save to team memory')
      term.writeln('\x1b[32m    memories \x1b[90m<query>\x1b[0m    Search archived memories')
      term.writeln('\x1b[32m    recent\x1b[0m               View recent Q&A')
      term.writeln('\x1b[32m    memory\x1b[0m               View memory entries')
      term.writeln('\x1b[32m    clear\x1b[0m                Clear terminal')
      term.writeln('\x1b[32m    help\x1b[0m                 Show this help')
      writePrompt()
      return
    }

    if (command === 'clear') {
      term.clear()
      WELCOME_LINES.forEach(line => term.writeln(line))
      writePrompt()
      return
    }

    // Execute command via API
    try {
      term.writeln('\r\n\x1b[33mExecuting...\x1b[0m')
      const result = await onCommand(command)

      // Write result with color
      const lines = result.split('\n')
      lines.forEach(line => {
        term.writeln(`\r\n${line}`)
      })
    } catch (error) {
      term.writeln(`\r\n\x1b[31mError: ${error.message}\x1b[0m`)
    }

    writePrompt()
  }

  return (
    <div className="terminal-container">
      <div ref={terminalRef} className="terminal" />
    </div>
  )
}

export default Terminal
