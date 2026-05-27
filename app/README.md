# Cortex OS Assistant - Desktop Application

## Project Overview
Desktop application built with **Next.js** and **Electron**. It provides an intuitive interface for interacting with the Cortex AI backend, acting as your personal `AI voice assistant`. 

### Key features
- Real-time two-way voice streaming with Voice Activity Detection (VAD)
- Dynamic 3D visual feedback (Assistant Orb)
- Conversation history
- Task and reminder management
- Configurable settings
- Secure OAuth authentication.

## 2. Module Directory

The `@app` directory contains both the Electron shell and the Next.js React frontend.

```text
app/
├── electron/          # Electron main process and IPC handlers
│   ├── main.ts        # Window initialization, deep linking, and protocol handling
│   ├── preload.ts     # Secure context bridge between React and Electron
│   ├── api.ts         # IPC handlers for mic, audio, and auth flows
│   └── audio/         # Audio recording, SoX integration, and VAD processing
├── public/            # Static assets, SVG icons, and application logos
└── src/
    ├── app/           # Next.js App Router structure
    │   ├── history/   # Past conversation sessions
    │   ├── profile/   # User profile and usage stats
    │   ├── settings/  # Configurable preferences (audio, scheduler, region)
    │   ├── tasks/     # Automated tasks and user-scheduled reminders
    │   └── Home.tsx   # Main interface with 3D Orb and active chat
    ├── components/    # Reusable React components (Sidebar, ChatHistory, Login, etc.)
    │   ├── audio/     # PCM Audio Player and Audio Manager hooks
    │   └── socket/    # WebSocket handlers for real-time audio/event streaming
    ├── hooks/         # SWR-based hooks for API interactions (`useApi.ts`)
    └── utility/       # API client configuration and UI tool badges
```

## 3. Settings Page Configurations

The **Settings** page allows users to customize their interaction with Cortex. Configurations are synchronized with the backend.

- **Cortex Interaction:**
  - **Wait Timeout:** Configures how many seconds (0-30s) Cortex waits for you to finish speaking before responding.
  - **Force Audio Reminder:** When enabled, Cortex forces the conversation WebSocket to open to announce reminder notifications via audio.
- **Scheduler Configs:**
  - **Reminder Buffer Time:** The number of minutes before an event's trigger time that Cortex should start reminding you.
- **Regional Settings:**
  - **Timezone Mode:** Choose `AUTO` for dynamic detection or `MANUAL` to explicitly set your local timezone.
- **Audio Devices:**
  - **Microphone:** Select your preferred input device for voice commands.
  - **Speaker:** Select your preferred output device for Cortex's audio responses.

## 4. Surfing Through the Application

Once authenticated via Google OAuth, you will enter the main application, starting on the **Home** interface:

1. **Home:** The central hub where you start/stop conversations. A 3D Orb dynamically reacts to Cortex's state (Listening, Thinking, Speaking). The right panel holds your active session's chat history and allows title editing.
2. **Conversations (History):** Accessible from the sidebar, this view lists your past sessions. Clicking a session changes the active context, loading its history on the Home view.
3. **Tasks:**
   - **Automated Tasks:** Review background tools and processes invoked by Cortex during your sessions.
   - **User Events:** Manage scheduled reminders and track their trigger times.
4. **Profile:** Review your account details, creation date, and total usage statistics (sessions, reminders).
5. **Settings:** Adjust your hardware, regional, and assistant interaction preferences.

## 5. Developer Guide: Starting the Application

### Prerequisites
- **Node.js 20+**
- Backend server running (Default: `http://127.0.0.1:8000`)
- `SoX` (Sound eXchange) installed and accessible in the system PATH (used by `node-audiorecorder`).

### Installation
Open your terminal in the `app` directory and install dependencies:
```bash
npm install
```

### Commands

To start or build the application, use the following npm scripts (referencing `package.json`):

- **Run in Development:**
  Starts the Next.js web UI on `http://localhost:3000`, watches Electron files, and opens the Electron desktop shell.
  ```bash
  npm run dev
  ```
- **Run Web UI Only:**
  Starts only the Next.js web server.
  ```bash
  npm run dev:web
  ```
- **Build the Application:**
  Compiles Next.js (exporting static files) and builds the Electron TypeScript files.
  ```bash
  npm run build
  ```
- **Package for Distribution:**
  Packages the compiled application into OS-specific installers.
  ```bash
  npm run dist         # Auto-detect OS
  npm run dist:win     # Create Windows (.exe) installer
  npm run dist:mac     # Create macOS (.dmg) installer
  npm run dist:linux   # Create Linux (.AppImage) installer
  ```
