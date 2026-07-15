# TeamAgent Web Showcase Guide

Complete guide for demonstrating TeamAgent's collaborative memory and real-time features.

## 🎯 Demo Scenarios

### Scenario 1: The Variable Problem (Your Example)

**Goal:** Show instant memory recall between engineers

**Terminal A (Alice):**
```
ask variable x equals 10
```
*Memory logs: "Alice asked about variable x"*

**Terminal B (Bob):**
```
search variable
```
*Instantly finds Alice's question!*

```
ask what is variable x plus 5
```
*The answer would be 15 if AI is connected*

**Key Points:**
- ✓ Engineer B can immediately access Engineer A's context
- ✓ No manual handoff needed
- ✓ Memory persists across sessions

---

### Scenario 2: API Documentation Chain

**Terminal A:**
```
ask What is the authentication endpoint?
```
*Sidebar shows: New question from A*

**Terminal B:**
```
search authentication
```
*Finds the question immediately*

**Terminal A:**
```
ask The auth endpoint is POST /api/v1/auth/login with username and password
```

**Terminal B:**
```
search endpoint
```
*Now sees both the question and answer*

**Key Points:**
- ✓ Real-time knowledge building
- ✓ Searchable Q&A archive
- ✓ Attribution tracking (who asked/answered)

---

### Scenario 3: Bug Investigation Collaboration

**Terminal A:**
```
ask Found bug in payment processing - orders not updating status
```

**Terminal B (different engineer, same day):**
```
search payment
```
*Immediately aware of the bug*

```
ask Is this related to the Redis timeout issue?
```

**Both engineers can now see:**
- Original bug report
- Follow-up question
- Connection between issues

**Key Points:**
- ✓ Instant bug awareness across team
- ✓ Context threading
- ✓ Prevents duplicate work

---

### Scenario 4: Onboarding New Engineer

**Terminal A (Senior Engineer):**
```
ask How do we handle rate limiting?
ask Use redis-py with sliding window algorithm, 100 req/min per user
```

**Terminal B (New Engineer, next day):**
```
search rate limiting
```
*Gets instant answer from archived Q&A*

```
recent
```
*Sees all recent team discussions*

**Key Points:**
- ✓ Self-service onboarding
- ✓ Persistent team knowledge
- ✓ Reduces repeated questions

---

## 🎨 Visual Features to Highlight

### 1. Split Terminal View
- Side-by-side engineers working simultaneously
- Different colors per engineer (A=green, B=cyan)
- Real xterm.js terminals (not fake mockups)

### 2. Live Memory Feed
- Right sidebar shows real-time activity
- Color-coded by engineer
- Timestamps on all events
- Smooth animations for new entries

### 3. Q&A Archive Tab
- Searchable knowledge base
- Status indicators (✓ answered, ? open)
- Full question/answer history
- Chronological ordering

### 4. Memory Stats
- Live event counter
- Q&A archive size
- Updates in real-time

---

## 📊 Demo Flow (Recommended Order)

### Part 1: Introduction (30 seconds)
1. Show the split terminal interface
2. Point out Engineer A and Engineer B
3. Highlight the Memory Sidebar
4. Mention it's all real-time

### Part 2: Basic Collaboration (1 minute)
1. **Terminal A:** `ask variable x equals 10`
2. Show sidebar update
3. **Terminal B:** `search variable`
4. Show instant result
5. **Terminal B:** `ask what is x plus 5`
6. Explain how B has A's context

### Part 3: Q&A Archive (1 minute)
1. Switch to "Q&A Archive" tab in sidebar
2. Show all questions/answers
3. **Terminal A:** `recent`
4. Compare terminal output with sidebar
5. Highlight persistence

### Part 4: Real-time Sync (30 seconds)
1. Type rapidly in Terminal A
2. Watch sidebar update in real-time
3. Type in Terminal B
4. Show both feeds merging

### Part 5: Search Power (30 seconds)
1. **Terminal B:** `search database`
2. Show multiple results if any exist
3. Explain FTS5 full-text search
4. Highlight relevance ranking

---

## 🎤 Key Talking Points

### Memory Prowess
> "Every question asked by Engineer A is instantly searchable by Engineer B. No Slack messages, no emails, no wiki updates - it's automatic."

### Collaboration Feature
> "Two engineers can work in the same terminal environment simultaneously. When Alice asks a question at 9 AM, Bob can search for it at 9:01 AM."

### Attribution
> "TeamAgent tracks who asked what and when. You can see Alice's questions, Bob's answers, and build a knowledge graph of your team."

### Persistence
> "Close the browser, come back tomorrow - all the memory is still there. SQLite + Mnemosyne ensures nothing is lost."

### Real-time
> "WebSocket connections mean updates are instant. No refresh needed. Watch the right sidebar - it updates live as commands execute."

---

## 🔧 Technical Implementation to Mention

### Frontend
- React 18 + Vite for fast dev
- xterm.js for authentic terminal UI
- WebSocket for real-time updates
- Clean separation: Terminal component, Memory component

### Backend
- FastAPI (modern Python web framework)
- WebSocket broadcast manager
- Direct integration with TeamAgent core
- REST API + WebSocket hybrid

### Data Layer
- SQLite with FTS5 full-text search
- Mnemosyne memory banks (BEAM architecture)
- Engineer profiles and teams
- Q&A archive with attribution

---

## 🚀 Advanced Demo Features

### 1. Command History
Both terminals support up/down arrow keys for command history (when implemented).

### 2. Multi-tab Support
Open multiple browser tabs - all stay synced via WebSocket.

### 3. Mobile Responsive
The UI works on tablets and phones (with horizontal layout on small screens).

### 4. Persistent Sessions
Engineers A and B are auto-created and persisted. Refresh the page - same engineers.

---

## 📝 Customization for Different Audiences

### For Developers
- Focus on: Real-time sync, terminal UI, WebSocket
- Show: API endpoints, code structure
- Emphasize: Easy to extend, modern stack

### For Product Managers
- Focus on: Collaboration, knowledge sharing
- Show: Use cases (bug tracking, onboarding)
- Emphasize: Productivity gains, reduced silos

### For C-Suite
- Focus on: Team efficiency, knowledge retention
- Show: Stats (questions answered, time saved)
- Emphasize: ROI, competitive advantage

---

## 🎬 Recording Tips

### Screen Recording
- Record at 1920x1080 minimum
- Show full browser window
- Use browser zoom (125%) for better visibility
- Keep mouse movements smooth

### Audio Narration
- Test microphone levels first
- Speak slowly and clearly
- Pause between scenarios
- Highlight key moments

### Video Editing
- Add annotations for key features
- Slow-mo the real-time updates
- Add timestamps for each scenario
- Include captions for accessibility

---

## 🐛 Common Issues During Demo

### WebSocket not connecting
- Check backend is running: `curl http://localhost:8000`
- Open browser console, look for WS errors
- Restart both servers with `./stop.sh && ./start.sh`

### Search returns no results
- FTS5 requires some data first
- Run `ask` command to create entries
- Check database exists: `ls ../data/teamagent.db`

### Terminal not displaying
- Check browser console for xterm errors
- Clear browser cache
- Try different browser (Chrome recommended)

### Commands not executing
- Verify backend API is responding
- Check network tab in browser dev tools
- Look at backend.log for errors

---

## 📈 Metrics to Track (Future)

Once deployed, track:
- Questions asked per day
- Search queries per engineer
- Average response time to questions
- Most searched terms
- Active engineers per team
- Memory retention rate

---

## 🌟 Future Showcase Ideas

### AI Integration
Connect to Red Hat Claude API:
- Engineer A asks: "What is variable x?"
- AI automatically answers AND saves to memory
- Engineer B benefits from AI + team knowledge

### File Sharing
Engineers can share code snippets:
```
share main.py
```
Other engineer sees syntax-highlighted code.

### Voice Commands
Use Web Speech API:
- Speak: "Ask about authentication"
- Terminal executes: `ask about authentication`

### Gamification
- Badges for answering questions
- Leaderboards for contributions
- Team knowledge score

### Mobile App
Native mobile terminals for on-the-go collaboration.

---

## ✅ Pre-Demo Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Database initialized with sample data
- [ ] Browser console clear (no errors)
- [ ] WebSocket connected (check network tab)
- [ ] Memory sidebar showing stats
- [ ] Both terminals responsive
- [ ] Screen recording software ready
- [ ] Microphone tested
- [ ] Demo script reviewed

---

## 🎓 Learning Resources

Share these with interested viewers:

- **TeamAgent Repo:** GitHub link to code
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **xterm.js:** https://xtermjs.org
- **WebSocket Guide:** MDN WebSocket API
- **React Docs:** https://react.dev
- **Mnemosyne Memory:** BEAM architecture papers

---

**Ready to showcase? Run `./start.sh` and open http://localhost:3000**

Good luck with your demo! 🚀
