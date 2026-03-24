const { ipcMain } = require("electron");
const { AudioManager } = require("./audio");

const audioManager = new AudioManager();

function registerIpcHandlers() {
  ipcMain.handle("assistant:mic-start", async (event, options = {}) => {
    audioManager.stopMicRecorder();

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
      audioManager.stopMicRecorder();
      return {
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  });

  ipcMain.handle("assistant:mic-stop", async () => {
    audioManager.stopMicRecorder();
    return { ok: true };
  });
}

module.exports = {
  registerIpcHandlers,
  audioManager,
};

export {};