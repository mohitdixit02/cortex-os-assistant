const { contextBridge, ipcRenderer } = require("electron");

const rendererApi = {
  pingBackend: (backendUrl) => ipcRenderer.invoke("assistant:ping-backend", backendUrl),
  startMicRecording: (options) => ipcRenderer.invoke("assistant:mic-start", options),
  stopMicRecording: () => ipcRenderer.invoke("assistant:mic-stop"),
  onMicChunk: (handler) => {
    const listener = (_event, chunk) => handler(chunk);
    ipcRenderer.on("assistant:mic-chunk", listener);
    return () => ipcRenderer.removeListener("assistant:mic-chunk", listener);
  },
  onMicError: (handler) => {
    const listener = (_event, error) => handler(error);
    ipcRenderer.on("assistant:mic-error", listener);
    return () => ipcRenderer.removeListener("assistant:mic-error", listener);
  },
  
  // Auth API
  openExternal: (url) => ipcRenderer.invoke("auth:open-external", url),
  onAuthRedirect: (handler) => {
    const listener = (_event, url) => handler(url);
    ipcRenderer.on("auth:redirect", listener);
    return () => ipcRenderer.removeListener("auth:redirect", listener);
  }
};

const rendererAPIName = "assistantAPI";

contextBridge.exposeInMainWorld(rendererAPIName, rendererApi);

export {};
