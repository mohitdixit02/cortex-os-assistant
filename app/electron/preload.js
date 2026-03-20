const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("assistantAPI", {
  pingBackend: (backendUrl) => ipcRenderer.invoke("assistant:ping-backend", backendUrl),
});