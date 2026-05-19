import { useEffect, useRef, useCallback, useState, useMemo } from "react";
import { useAudioWebSocket } from "./AudioWebSocket";
import { useEventWebSocket } from "./EventWebSocket";
import { useAppContext } from "../AppContext";
import { toast } from "react-toastify";
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

    const { user, activeThreadId } = useAppContext();
    const userId = user?.id || user?.user_id;
    const [isConversationActive, setIsConversationActive] = useState(false);
    
    const audioStreamSession: AudioStreamSession = useMemo(() => ({
        baseUrl,
        binaryType: BINARY_TYPE,
        userId,
    }), [baseUrl, userId]);

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
        sendEventMessage
    } = useEventWebSocket(baseUrl);

    const detachAudioRef = useRef<(() => void) | null>(null);
    const wasForceOpenedRef = useRef(false);

    const endAudioStream = useCallback(async () => {
        await stopAudioStreaming();
        setIsConversationActive(false);
        if (detachAudioRef.current) {
            detachAudioRef.current();
            detachAudioRef.current = null;
        }
        closeAudioSocket();
    }, [stopAudioStreaming, closeAudioSocket]);

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
        const detach = await attachAudioListener(() => {
            if (wasForceOpenedRef.current) {
                console.log("Forced audio socket detected: closing after playback drain.");
                endAudioStream();
                wasForceOpenedRef.current = false;
            }
        });
        detachAudioRef.current = detach;
    }, [userId, startAudioStreaming, attachAudioListener, endAudioStream]);

    const onEventMessage = useCallback(async (event: MessageEvent) => {
        if (typeof event.data !== "string") return;
        try {
            const data = JSON.parse(event.data);
            console.log("Received event message:", data);

            if (data.type === "reminder" && data.stage === "triggered") {
                console.log("Triggering reminder notification:", data.message);
                
                const notificationTitle = "Reminder";
                const notificationBody = data.message || "A reminder has been triggered";

                // Show native desktop notification
                if (Notification.permission === "granted") {
                    console.log("Notification permission granted, showing...");
                    try {
                        new Notification(notificationTitle, {
                            body: notificationBody,
                            // Removed icon to avoid path resolution issues
                        });
                    } catch (err) {
                        console.error("Error creating native notification:", err);
                    }
                } else if (Notification.permission !== "denied") {
                    console.log("Notification permission not granted, requesting...");
                    const permission = await Notification.requestPermission();
                    if (permission === "granted") {
                        new Notification(notificationTitle, {
                            body: notificationBody
                        });
                    }
                } else {
                    console.warn("Notification permission is denied");
                }

                // UI Fallback (Toast)
                toast.info(notificationBody, {
                    position: "top-right",
                    autoClose: 10000,
                    hideProgressBar: false,
                    closeOnClick: true,
                    pauseOnHover: true,
                    draggable: true,
                });
            }

            if (data.type === "audio_socket" && data.stage === "open_request") {
                console.log("Received request to force open audio websocket");
                if (isConversationActive) {
                    sendEventMessage({ type: "WEBSOCKET_OPEN_TRUE" });
                    return;
                }

                try {
                    // Start audio streaming using activeThreadId or a default fallback
                    const sessionId = activeThreadId || "background-reminder-session";
                    console.log(`Force-opening audio socket with session: ${sessionId}`);
                    wasForceOpenedRef.current = true;
                    await startAudioStream(sessionId);
                    sendEventMessage({ type: "WEBSOCKET_OPEN_TRUE" });
                } catch (err) {
                    console.error("Failed to force open audio websocket:", err);
                    sendEventMessage({ type: "WEBSOCKET_OPEN_FALSE" });
                    if (Notification.permission === "granted") {
                        new Notification("Error", {
                            body: "Failed to open microphone for reminder audio."
                        });
                    }
                }
            }
        } catch (err) {
            console.error("Error parsing event socket message:", err);
        }
    }, [isConversationActive, startAudioStream, sendEventMessage, activeThreadId]);

    // Event socket setup on Init and cleanup on unmount
    useEffect(() => {
        let detachEvent: (() => void) | undefined;

        const setupEventSocket = async () => {
            if (userId) {
                const detach = await attachEventListener({ 
                    userId, 
                    onMessage: onEventMessage 
                });
                detachEvent = detach;
            }
        };
        setupEventSocket();

        return () => {
            if (detachEvent) detachEvent();
        };
    }, [userId, attachEventListener, onEventMessage]);

    // Independent cleanup for Audio Socket on Unmount
    useEffect(() => {
        return () => {
            closeAudioSocket();
            if (detachAudioRef.current) {
                detachAudioRef.current();
                detachAudioRef.current = null;
            }
        };
    }, [closeAudioSocket]);

    return {
        startAudioStream,
        endAudioStream,
        isConversationActive,
        isListening,
        isSpeaking
    };
};
