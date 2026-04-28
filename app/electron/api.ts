const { ipcMain, shell } = require("electron");
const { AudioManager } = require("./audio");

const audioManager = new AudioManager();

function registerIpcHandlers() {
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

  // Auth: Open external URL for OAuth
  ipcMain.handle("auth:open-external", async (event, url) => {
    await shell.openExternal(url);
  });
}

module.exports = {
  registerIpcHandlers,
  audioManager,
};

export {};
