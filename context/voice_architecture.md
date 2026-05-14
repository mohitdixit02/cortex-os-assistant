# Voice Streaming Architecture
This file outlines the architecture for handling voice streaming between user (Electron based desktop app) and the Cortex server.

### User Specifc Events - (UI -> Cortex Server)
`UserSpeechStartEvent` - Triggered when user starts speaking (handled by VAD in the Electron app)
`UserSpeechEndEvent` - Triggered when user stops speaking (handled by VAD in the Electron app)
`AIStartSpeakingEvent` - Triggered when AI starts speaking in app - Send back to Cortex Server from Electron app when PCM Player starts playing the audio stream received from the server. Only send after receiving `AI_AUDIO_STREAM_START` event from the server, which indicates that the server has started sending audio data to the Electron app.
`AIStopSpeakingEvent` - Triggered when AI stops speaking - Send back to Cortex Server from Electron app when PCM Player stops playing the audio stream received from the server. Only send after receiving `AI_AUDIO_STREAM_END` event from the server, which indicates that the server has finished sending audio data to the Electron app, and the app has finished playing the audio stream.

### Server Specifc Events (Cortex Server -> UI)
`CONVERSATION_START` - Sent as acknowledgement when the Audio Stream Socket is established and ready to receive audio data, after user clicks on Start Conversation button.
`CONVERSATION_END` - Sent when the conversation ends by clicking on Stop Conversation button.
`IS_LISTENING` - Sent when the server is ready to receive audio data (after receiving UserSpeechStartEvent and VAD detects speech).
`FINISHED_LISTENING` - Sent when the server has finished processing the received audio data (after receiving UserSpeechEndEvent and VAD detects end of speech).
`REMINDER_EVENT` - Contains info about reminder which will be shown as a toast notification in the Electron app (received from Cortex server).
`AI_AUDIO_STREAM_START` - Sent when the server starts sending audio data to the Electron app to play. Includes the configuration info of the PCM Player (e.g., sample rate, number of channels, etc.) that the Electron app needs to configure before playing the audio stream. Also include whether stream is task stream or reminder stream.
`AI_AUDIO_STREAM_END` - Sent when the server finishes sending audio data to the Electron app. (It is independent of whether the AI has finished speaking or not.)

### Sockets
1. Audio Stream Socket
- Purpose: To stream raw audio data between the Electron app and the Cortex server in both directions.
- Server sends info of PCM Player configuration before streaming starts, so that Electron app can configure its PCM Player accordingly.

2. Event Stream Socket
- Purpose: To send and receive real-time events related to voice interactions (e.g., start/stop speaking, errors, etc.) between the Electron app and the Cortex server.
- Server sends event data to the Electron app, and the Electron app can also send events to the server.

## Socket Initilization
- When the Electron app starts, it establishes a connection to the Cortex server for the Event Stream Socket.
- The Audio Stream Socket is established when the user clicks on the Start Conversation button. It is closed when the user clicks on the Stop Conversation button.
- The Event Stream Socket remains open as long as the Electron app is running to allow for real-time event communication.
- Event Stream Socket can forcily re-open the Audio Strem Socket in case `AI_AUDIO_STREAM_START` event is recevied with reminder stream, and audio stream is closed. Only done if configuration is done in settings. (Will be implemented in later phase)

## Event Flags in Server
1. `is_user_speaking` - Indicates whether the user is currently speaking (set to true when receiving UserSpeechStartEvent, set to false when receiving UserSpeechEndEvent).
2. `is_ai_speaking` - Indicates whether the AI is currently speaking (set to true when receiving AIStartSpeakingEvent, set to false when receiving AIStopSpeakingEvent).

## Server Streaming Architecture
- A process will listen continuously to the Redis DB:2 for result, and check for two event flags: `is_user_speaking` and `is_ai_speaking`.
- Only when both the flags are released (marked as false), process will start streaming the audio data to the Electron app, and set `is_ai_speaking` flag to true. This is to make sure that there is no overlap between user speech and AI speech, and to avoid sending audio stream to the Electron app when user is still speaking.
- When the process detects that the audio stream has finished (based on the data in Redis DB:2), it will send `AI_AUDIO_STREAM_END` event to the Electron app.
- When the process receives `AIStopSpeakingEvent` from the Electron app, it will set `is_ai_speaking` flag to false, which will allow the next audio stream to be sent to the Electron app when it is ready.

## Objective
1. Understand the architecture and plan-out how to implement the feature (both server and client side).
2. Also decide, Server Streaming Architecture - whether to use a separate process, asycnio loop, or worker process apart from server, etc.
3. also decide the implementation of each websockt connection in both UI and backend.
4. Also consider, StreamLock to manage the streaming process and avoid race conditions and conflict between two streams.
