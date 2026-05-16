const EventType = {
    META_DATA: "metaData",
    AUDIO_END: "audioEnd",
    CONVERSATION_START: "ConversationStart",
    CONVERSATION_END: "ConversationEnd",
    USER_START_SPEAKING: "UserSpeechStartEvent",
    USER_STOP_SPEAKING: "UserSpeechEndEvent",
    AI_START_SPEAKING: "AIStartSpeakingEvent",
    AI_STOP_SPEAKING: "AIStopSpeakingEvent",
    AUDIO_CHUNK: "audioChunk",
} as const;

const emitEventSocket = (eventSocket: WebSocket | null, type: typeof EventType[keyof typeof EventType]) => {
    if (eventSocket && eventSocket.readyState === WebSocket.OPEN) {
        eventSocket.send(JSON.stringify({ type }));
    } else {
        console.warn(`Cannot emit event "${type}", socket is not open`);
    }
};

const emitAudioSocket = (
    audioSocket: WebSocket | null,
    type: typeof EventType[keyof typeof EventType],
    payload?: any,
) => {
    if (audioSocket && audioSocket.readyState === WebSocket.OPEN) {
        if (type === EventType.AUDIO_CHUNK) {
            if(!payload) {
                console.warn("Audio chunk is missing for AUDIO_CHUNK event");
                return;
            }
            if(!(payload instanceof ArrayBuffer)) {
                console.warn("Payload for AUDIO_CHUNK event should be an ArrayBuffer");
                return;
            }
            audioSocket.send(payload);
        } else {
            if (payload) {
                audioSocket.send(JSON.stringify({ type, ...payload }));
            }
            else{
                audioSocket.send(JSON.stringify({ type }));
            }
        }
    } else {
        console.warn("Cannot send audio chunk, socket is not open");
    }
};

const Emitter = {
    EventType,
    emitAudioSocket,
    emitSocketEvent: emitEventSocket,
};

export default Emitter;