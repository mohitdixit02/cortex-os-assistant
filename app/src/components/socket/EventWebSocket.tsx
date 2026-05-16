import { useEffect, useRef, useState, useCallback } from "react";
import { configureWebSocket } from "./utility";
import { handleEventMessage } from "./handlers";

type EventListenerProps = {
    userId: string;
    sessionId?: string;
}

export const useEventWebSocket = (
    baseUrl?: string,
) => {
    if (!baseUrl) {
        throw new Error("WebSocket base URL is required");
    }
    const eventSocketRef = useRef<WebSocket | null>(null);;
    const attachEventListener = useCallback(async (
        { userId }: EventListenerProps
    ) => {
        const eventUrl = `${baseUrl}/event?user_id=${userId}`;
        if (!eventSocketRef.current || eventSocketRef.current.readyState !== WebSocket.OPEN) {
            eventSocketRef.current = await configureWebSocket(null, eventUrl, "blob");
        }
        const eventSocket = eventSocketRef.current;
        if (eventSocket) {
            eventSocket.addEventListener("message", handleEventMessage);
        }
        return () => {
            eventSocket?.removeEventListener("message", handleEventMessage);
        };
    }, [baseUrl]);

    return {
        attachEventListener,
    }
};