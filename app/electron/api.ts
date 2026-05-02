import { ipcMain, shell, BrowserWindow } from "electron";
import { AudioManager } from "./audio";

const audioManager = new AudioManager();

export function registerIpcHandlers() {
  console.log("[Main] Registering IPC handlers...");
  ipcMain.handle("assistant:mic-start", async (event, options = {}) => {
    await audioManager.stopMicRecorder();

    const recorderOptions = {
      program: "sox",
      bits: 16,
      channels: 1,
      encoding: "signed-integer",
      rate: 16000,
      type: "wav",
      silence: 0,
      ...options,
    };

    try {
      await audioManager.startMicStream({
        recorderOptions,
        event,
        streamRendererEndPoint:"assistant:mic-chunk",
        errorRendererEndPoint:"assistant:mic-error"
      });
      return { ok: true };
    } catch (error) {
      await audioManager.stopMicRecorder();
      return {
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  });

  ipcMain.handle("assistant:mic-stop", async () => {
    await audioManager.stopMicRecorder();
    return { ok: true };
  });

  // Auth: Open internal window for OAuth
  ipcMain.handle("auth:start-flow", async (event, url) => {
    console.log("[Main] Starting auth flow for URL:", url);
    const parent = BrowserWindow.fromWebContents(event.sender);
    const authWindow = new BrowserWindow({
      width: 600,
      height: 700,
      parent: parent || undefined,
      modal: true,
      show: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
      },
    });

    // Some Google OAuth flows might require a specific User-Agent
    authWindow.webContents.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    );

    authWindow.loadURL(url);
    authWindow.once("ready-to-show", () => authWindow.show());

    return new Promise((resolve) => {
      const handleNavigation = (navUrl: string) => {
        console.log("[Main] Auth window navigating to:", navUrl);
        if (navUrl.startsWith("cortex-ai://") || navUrl.includes("code=")) {
          resolve({ url: navUrl });
          authWindow.destroy();
        }
      };

      authWindow.webContents.on("will-navigate", (e, navUrl) => handleNavigation(navUrl));
      authWindow.webContents.on("will-redirect", (e, navUrl) => handleNavigation(navUrl));

      authWindow.on("closed", () => {
        resolve({ error: "Window closed by user" });
      });
    });
  });

  // Auth: Open external URL (keep for general use)
  ipcMain.handle("auth:open-external", async (event, url) => {
    await shell.openExternal(url);
  });
}

export { audioManager };

