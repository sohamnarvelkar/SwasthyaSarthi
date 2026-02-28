# SwasthyaSarthi Frontend

A production-grade Next.js + React frontend for the SwasthyaSarthi multi-agent AI pharmacy system.

## Features

- **Modern ChatGPT-style UI** - Clean, professional interface with dark/light theme
- **Continuous Voice Agent** - Hands-free conversation using Web Speech API
- **Multilingual Support** - Automatic language detection (English, Hindi, Marathi)
- **ElevenLabs TTS** - Human-quality voice output for responses
- **Real-time Chat** - Text interaction with AI agents
- **Conversation History** - Persistent chat sessions with sidebar navigation

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Styling**: TailwindCSS
- **Icons**: Lucide React
- **State Management**: React Hooks

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running on http://localhost:8000

### Installation

```
bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Configuration

### Environment Variables

Create a `.env.local` file in the frontend directory:

```
env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Architecture

```
frontend/
├── app/                 # Next.js App Router
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Main page
│   └── globals.css     # Global styles
├── components/         # React components
│   ├── ChatWindow.tsx     # Main chat interface
│   ├── MessageBubble.tsx  # Chat message display
│   ├── VoiceAgentButton.tsx # Voice mode toggle
│   ├── VoiceVisualizer.tsx  # Voice animations
│   ├── Sidebar.tsx        # Conversation list
│   └── LanguageIndicator.tsx # Language selector
├── hooks/             # Custom React hooks
│   ├── useChat.ts       # Chat state management
│   └── useVoiceAgent.ts # Voice agent logic
└── services/          # API services
    └── api.ts          # REST API client
```

## Voice Agent Flow

1. User clicks "Start Voice Agent"
2. Browser requests microphone access
3. Speech recognition starts (Web Speech API)
4. User speaks - transcript captured in real-time
5. Transcript sent to `/voice` API endpoint
6. Backend processes through LangGraph agents
7. ElevenLabs generates audio response
8. Audio auto-plays on frontend
9. System automatically starts listening again
10. Loop continues until user stops

## API Endpoints

The frontend communicates with these backend endpoints:

- `POST /chat` - Text chat interaction
- `POST /voice` - Voice interaction (returns text + audio)
- `GET /audio/{filename}` - Serve generated audio files
- `GET /conversations/{user_id}` - Get conversation history

## Browser Support

- Chrome (recommended for voice)
- Edge
- Firefox
- Safari (limited voice support)

## License

MIT
