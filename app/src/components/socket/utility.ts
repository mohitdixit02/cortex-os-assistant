const ensureSocketOpen = async (socket: WebSocket) => {
    if(!socket) {
        throw new Error("WebSocket is not initialized");
    }
    if (socket.readyState === WebSocket.OPEN) {
        return {
            ok: true,
            message: "WebSocket is already open",
        };
    }

    if (socket.readyState !== WebSocket.CONNECTING) {
        throw new Error("WebSocket is not connected");
    }

    await new Promise<void>((resolve, reject) => {
        const onOpen = () => {
            socket.removeEventListener("error", onError);
            resolve();
        };
        const onError = () => {
            socket.removeEventListener("open", onOpen);
            reject(new Error("Failed to open WebSocket"));
        };

        socket.addEventListener("open", onOpen, { once: true });
        socket.addEventListener("error", onError, { once: true });
    });
};

const initializeWebSocket = (socketUrl: string, binaryType: "arraybuffer" | "blob") => {
    const socket = new WebSocket(socketUrl);
    socket.binaryType = binaryType;
    return socket;
}

/**
### Configure a WebSocket connection
#### Arguments
- `socket`: The existing WebSocket instance, or null if not initialized
- `socketUrl`: The URL to connect the WebSocket to
- `binaryType (optional)`: The type of binary data expected ("arraybuffer" or "blob") - only for audio socket
**/
export const configureWebSocket = async (
    socket: WebSocket | null,
    socketUrl: string,
    binaryType?: "arraybuffer" | "blob"
) => {
    let activeSocket = socket;
    if (!activeSocket || activeSocket.readyState === WebSocket.CLOSING || activeSocket.readyState === WebSocket.CLOSED) {
        activeSocket = initializeWebSocket(socketUrl, binaryType);
    }
    await ensureSocketOpen(activeSocket); // throws error if socket fails to open
    console.log("WebSocket connected successfully");
    return activeSocket;
}

