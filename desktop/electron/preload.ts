import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron'

// --------- Expose some API to the Renderer process ---------
contextBridge.exposeInMainWorld('ipcRenderer', {
    on(channel: string, listener: (event: IpcRendererEvent, ...args: any[]) => void) {
        ipcRenderer.on(channel, listener)
    },
    off(channel: string, listener: (event: IpcRendererEvent, ...args: any[]) => void) {
        ipcRenderer.off(channel, listener)
    },
    send(channel: string, ...args: any[]) {
        ipcRenderer.send(channel, ...args)
    },
    invoke(channel: string, ...args: any[]) {
        return ipcRenderer.invoke(channel, ...args)
    },
})
