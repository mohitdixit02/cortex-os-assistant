import { useEffect, useRef, useCallback, useState } from "react";
import { useAudioWebSocket } from "./AudioWebSocket";
import { useEventWebSocket } from "./EventWebSocket";
import { useAppContext } from "../AppContext";
import { 
    AudioStreamSession,
    BINARY_TYPE
 } from "./types";

export const useWebSocket = (
    baseUrl?: string,
) => {
    if (!baseUrl) {
        throw new Error("WebSocket base URL is required");
    }

    const { user } = useAppContext();
    const userId = user?.id || user?.user_id;
    const [isConversationActive, setIsConversationActive] = useState(false);
    const audioStreamSession: AudioStreamSession = {
        baseUrl,
        binaryType: BINARY_TYPE,
        userId,
    };

    // Audio Socket
    const {
        startAudioStreaming,
        stopAudioStreaming,
        attachAudioListener,
        closeAudioSocket,
        isListening,
        isSpeaking
    } = useAudioWebSocket(audioStreamSession);

    // Event Socket
    const {
        attachEventListener,
    } = useEventWebSocket(baseUrl);

    const detachAudioRef = useRef<(() => void) | null>(null);

    // Event socket setup on Init and cleanup on unmount
    useEffect(() => {
        let detachEvent: (() => void) | undefined;

        const setupEventSocket = async () => {
            if (userId) {
                const detach = await attachEventListener({ userId });
                detachEvent = detach;
            }
        };
        setupEventSocket();

        return () => {
            if (detachEvent) detachEvent();
            closeAudioSocket();
            if (detachAudioRef.current) {
                detachAudioRef.current();
                detachAudioRef.current = null;
            }
        };
    }, [userId, attachEventListener, closeAudioSocket]);

    // Set isConversationActive based on streaming ref changes
    const startAudioStream = useCallback(async (sessionId: string) => {
        // Cleanup previous audio listeners
        if (detachAudioRef.current) {
            detachAudioRef.current();
            detachAudioRef.current = null;
        }
        await startAudioStreaming(userId, sessionId);
        setIsConversationActive(true);

        // detach - used to remove the audio listener when the stream ends or component unmounts
        const detach = await attachAudioListener();
        detachAudioRef.current = detach;
    }, [userId, startAudioStreaming, attachAudioListener]);

    const endAudioStream = useCallback(async () => {
        await stopAudioStreaming();
        setIsConversationActive(false);
        if (detachAudioRef.current) {
            detachAudioRef.current();
            detachAudioRef.current = null;
        }
        closeAudioSocket();
    }, [stopAudioStreaming, closeAudioSocket]);

    return {
        startAudioStream,
        endAudioStream,
        isConversationActive,
        isListening,
        isSpeaking
    };
};
