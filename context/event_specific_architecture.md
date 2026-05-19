# Reminder Trigger Architecture
## Context
In the current implementation, we have two websockets: `Audio`, which is initialized when user clicks on the start conversation button, and `Event`, which is initialized as soon as application gets launched.
Also in settings there is a `force_open_websocket` config which is currently set to `False`. If set to `True`, it should open the `Audio websocket` in case it is not already open. This is required to ensure that reminder trigger works even when user has not started a conversation (and hence audio websocket is not open).

## Implementation
### Backend
In the `cortex_server`, result_worker continusoly listens to redis DB Pub/Sub stream for completed tasks. If task owner is `voice_client`, it is streamed to `Audio websocket`. If task owner is `event_tool`, it is currently streaming to Audio Socket. We need following changes in the backend.

1. By default, the event is sent on the Event Websocket using a common `UserVoiceState` to maintain the same state. A own `StreamEvent` and `StreamEventResponse` can be created for this purpose.
2. Create following events in the `StreamEventResponse` map:
   - `REMINDER_TRIGGERED`: This event is triggered when a reminder is triggered. It contains the reminder details and can be used to display a notification to the user.
   - `OPEN_AUDIO_WEBSOCKET`: This event is triggered when the `force_open_websocket` config is set to `True`.
   - Once, Backend recieves `WEBSOCKET_OPEN_TRUE` event from UI, it will stream the Audio using the existing `StreamAudio` event. Make sure it involve the same event methods like `AI_AUDIO_STREAM_START` and `AI_AUDIO_STREAM_END` to maintain the same flow.
    - If Backend receives `WEBSOCKET_OPEN_FALSE` event from UI, it will end the and continue for further processing without streaming audio.

### Frontend
1. In the UI `app` component, we need to listen to `Event Websocket` for the above mentioned events and handle them accordingly.
2. If `REMINDER_TRIGGERED` event is received, we can display a notification to the user. Notification should be throw native desktop based as application is electron based.
3. If `OPEN_AUDIO_WEBSOCKET` event is received, we need to check if Audio Websocket is already open. If not, we need to open the Audio Websocket and send `WEBSOCKET_OPEN_TRUE` event to Backend. If it is already open, we can directly send `WEBSOCKET_OPEN_TRUE` event to Backend.
4. If UI fail to open the Audio Websocket for any reason, it should send `WEBSOCKET_OPEN_FALSE` event to Backend. Also give the notification to user we fail to open Audio Websocket inspite of setting the `force_open_websocket` config to `True`. This will improve user experience.

Make sure that the above implementation is done in a way that it does not break the existing flow and is backward compatible. Also, ensure that the timezone consistency is maintained across the application for reminder trigger to work correctly.
