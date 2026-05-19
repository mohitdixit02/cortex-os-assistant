import asyncio
import json
from cortex_cm.redis.redis_client import RedisClient, RedisModeType
from cortex_cm.utility.logger import get_logger
from cortex_queue.dto import TaskItem, TaskStatus
from cortex_cm.pg.enums import TaskOwner
from .state_manager import voice_state_manager
from cortex_server.cortex.voice import VoiceClient
from service.stream.event import StreamEvent, ResponseKey, StreamEventResponse
from cortex_server.service.config_service import config_service
from uuid import UUID

logger = get_logger("RESULT_WORKER")

class ResultStreamWorker:
    """
    ### Result Stream Worker
    Uses Redis Pub/Sub to listen for completed tasks and streams results back to the user.
    """
    _instance = None
    _task = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResultStreamWorker, cls).__new__(cls)
        return cls._instance

    def start(self):
        """Starts the worker as a background task if not already running."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())
            logger.info("ResultStreamWorker (Pub/Sub) started.")

    async def stop(self):
        """Stops the background worker task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("ResultStreamWorker stopped.")

    async def _run_loop(self):
        redis_client = RedisClient.get_client(RedisModeType.RESULT)
        pubsub = redis_client.client.pubsub()
        
        # Subscribe to all user stream channels
        pubsub.psubscribe("user_stream:*")
        logger.info("Listening for task results via Redis Pub/Sub (user_stream:*)...")

        while True:
            try:
                # Check for new messages
                message = pubsub.get_message(ignore_subscribe_messages=True)
                if not message:
                    await asyncio.sleep(0.1)
                    continue

                # Parse the channel and data
                channel = message.get("channel")
                if isinstance(channel, bytes):
                    channel = channel.decode("utf-8")
                
                data_str = message.get("data")
                if not data_str:
                    continue
                
                data = json.loads(data_str)
                logger.info("Pub/Sub message received on channel %s for user %s", channel, data.get("metadata", {}).get("user_id"))
                
                task_item = TaskItem(
                    task_id=data.get("task_id"),
                    payload=data.get("payload"),
                    metadata=data.get("metadata", {}),
                    task_name=data.get("task_name"),
                    task_description=data.get("task_description"),
                    status=TaskStatus(data.get("status")),
                    result=data.get("result"),
                    error=data.get("error")
                )

                user_id = task_item.metadata.get("user_id")
                if not user_id:
                    logger.warning("Received task result without user_id in metadata: %s", data.get("task_id"))
                    continue

                # CRUCIAL: Only process if the user is connected to THIS server instance
                state = voice_state_manager.get_state(user_id)
                if not state.audio_socket and not state.event_socket:
                    logger.info("Ignoring result for user %s: No active sockets (audio: %s, event: %s)", 
                                 user_id, bool(state.audio_socket), bool(state.event_socket))
                    continue

                logger.info("Received result for OUR user %s from channel %s", user_id, channel)
                await self._process_task_result(user_id, task_item)

            except Exception as e:
                logger.error("Error in ResultStreamWorker loop: %s", str(e))
                await asyncio.sleep(1)

    async def _process_task_result(self, user_id: str, task_item: TaskItem):
        state = voice_state_manager.get_state(user_id)
        task_owner = task_item.metadata.get("task_owner")

        # 1. Handle Event/Reminder Notification via Event Socket
        if task_owner == TaskOwner.EVENT_TOOL.value and state.event_socket:
            logger.info("Sending reminder notification to user %s via event socket", user_id)
            event_response = StreamEventResponse(websocket=state.event_socket, streamEvent=StreamEvent(user_id=user_id))
            
            # Extract actual response text if result is a dict
            message_text = task_item.result
            if isinstance(message_text, dict):
                message_text = message_text.get("response") or message_text.get("message") or str(message_text)
            
            # Send the actual result from the task to the UI using standardized response
            await event_response.send_response(ResponseKey.REMINDER_TRIGGERED, message=message_text)

            # Check if we need to force open the audio websocket
            if not state.audio_socket:
                user_config = config_service.get_user_config(UUID(user_id))
                if user_config.force_open_websocket:
                    logger.info("force_open_websocket is True, requesting UI to open audio socket for user %s", user_id)
                    state.audio_ws_opened_event.clear()
                    state.audio_ws_success = False
                    await event_response.send_response(ResponseKey.OPEN_AUDIO_WEBSOCKET)
                    
                    try:
                        # Non-blocking wait for UI to open the socket
                        await asyncio.wait_for(state.audio_ws_opened_event.wait(), timeout=15.0)
                        if not state.audio_ws_success:
                            logger.warning("UI failed to open audio socket for user %s, skipping audio stream", user_id)
                            return
                    except asyncio.TimeoutError:
                        logger.warning("Timed out waiting for UI to open audio socket for user %s", user_id)
                        return

        # 2. Wait for Channel Clear (No one is speaking)
        while state.is_user_speaking or state.is_ai_speaking:
            await asyncio.sleep(0.2)

        # 3. Acquire Lock and Set AI Speaking State
        async with state.stream_lock:
            # Re-fetch state and verify sockets
            state = voice_state_manager.get_state(user_id)
            stream_client = state.stream_client
            if not stream_client or not state.audio_socket:
                logger.warning("User %s active context vanished or audio socket missing, dropping task result.", user_id)
                return

            stream_event = stream_client.get_stream_event()
            task_session_id = task_item.metadata.get("session_id")
            
            # Verify the session ID matches the currently active session
            if task_session_id and stream_event.session_id and str(stream_event.session_id) != str(task_session_id):
                logger.warning("Ignoring task result %s: Session mismatch (Task: %s, Active: %s)", 
                            task_item.task_id, task_session_id, stream_event.session_id)
                return

            logger.info("Streaming result for task %s to user %s (owner: %s)", task_item.task_id, user_id, task_owner)
            state.is_ai_speaking = True
            voice_client = stream_client.voiceClient
            
            event_response = StreamEventResponse(
                websocket=state.audio_socket,
                streamEvent=stream_event
            )

            try:
                # Notify UI that a stream is starting
                await event_response.send_response(ResponseKey.AI_AUDIO_STREAM_START)
                
                # Stream the audio
                await voice_client._handle_task_queue(task_item)
                
                # Notify UI that server finished sending audio
                await event_response.send_response(ResponseKey.AI_AUDIO_STREAM_END)
                
            except Exception as e:
                logger.error("Failed to stream task %s: %s", task_item.task_id, str(e))
            finally:
                state.is_ai_speaking = False

result_stream_worker = ResultStreamWorker()
