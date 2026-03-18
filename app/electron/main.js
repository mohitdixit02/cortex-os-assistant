const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");

const isDev = !app.isPackaged;
const startUrl = process.env.ELECTRON_START_URL || "http://localhost:3000";

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 960,
    minHeight: 640,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(startUrl);

  // Open DevTools in development mode - for debugging
  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: "detach" });
  }
}

ipcMain.handle("assistant:ping-backend", async (_event, backendUrl) => {
  const base = (backendUrl || "http://127.0.0.1:8000").replace(/\/$/, "");
    console.log(`Pinging backend at ${base}/health...`);

  try {
    // const response = await fetch(`${base}/health`, {
    //   method: "GET",
    // });

    // return {
    //   ok: response.ok,
    //   status: response.status,
    //   url: `${base}/health`,
    // };
    return {
        ok: true,
        status: 200,
        url: `${base}/health`,
        type: "mock",
    }
  } catch (error) {
    return {
      ok: false,
      status: null,
      url: `${base}/health`,
      error: error instanceof Error ? error.message : String(error),
    };
  }
});

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
