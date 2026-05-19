import { useEffect, useRef, useState, useCallback } from "react";
import { configureWebSocket } from "./utility";
import { handleEventMessage } from "./handlers";

type EventListenerProps = {
    userId: string;
    sessionId?: string;
    onMessage?: (event: MessageEvent) => void;
}

export const useEventWebSocket = (
    baseUrl?: string,
) => {
    if (!baseUrl) {
        throw new Error("WebSocket base URL is required");
    }
    const eventSocketRef = useRef<WebSocket | null>(null);;
    const attachEventListener = useCallback(async (
        { userId, onMessage }: EventListenerProps
    ) => {
        const eventUrl = `${baseUrl}/event?user_id=${userId}`;
        if (!eventSocketRef.current || eventSocketRef.current.readyState !== WebSocket.OPEN) {
            eventSocketRef.current = await configureWebSocket(null, eventUrl, "blob");
        }
        const eventSocket = eventSocketRef.current;
        if (eventSocket) {
            if (onMessage) {
                eventSocket.addEventListener("message", onMessage);
            } else {
                eventSocket.addEventListener("message", handleEventMessage);
            }
        }
        return () => {
            if (onMessage) {
                eventSocket?.removeEventListener("message", onMessage);
            } else {
                eventSocket?.removeEventListener("message", handleEventMessage);
            }
        };
    }, [baseUrl]);

    const sendEventMessage = useCallback((message: any) => {
        if (eventSocketRef.current && eventSocketRef.current.readyState === WebSocket.OPEN) {
            eventSocketRef.current.send(JSON.stringify(message));
        } else {
            console.warn("Event socket not open, cannot send message:", message);
        }
    }, []);

    return {
        attachEventListener,
        sendEventMessage
    }
};