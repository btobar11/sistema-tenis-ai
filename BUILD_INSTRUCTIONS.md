# Guía de Construcción: Desktop Client (.exe)

Sigue estos pasos para generar el ejecutable final de EDGESET Tenis.

## 1. Preparación del Entorno
El error de "Archivos bloqueados" o "Permisos" suele ocurrir porque VS Code o la terminal integrada tienen "agarrados" los archivos de la carpeta `dist`.

**Recomendación:** Cierra cualquier proceso de `npm run dev` que tengas corriendo en la terminal.

## 2. Instrucciones Paso a Paso (Terminal Externa)

1.  Abre **PowerShell** o **CMD** (Símbolo del sistema) como **Administrador**.
    *   *Click derecho en Inicio > Terminal (Admin) o PowerShell (Admin)*
2.  Navega a la carpeta del proyecto:
    ```powershell
    cd "c:\Users\benja\OneDrive\Escritorio\Sistema Tenis\desktop"
    ```
3.  Limpia instalaciones previas (opcional pero recomendado):
    ```powershell
    # Si usas PowerShell (lo más probable):
    Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force dist-electron -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force dist-release -ErrorAction SilentlyContinue

    # IMPORTANTE: Si recibes error de "File Used by another process":
    # Ejecuta esto para matar procesos zombis de Electron/Node:
    taskkill /F /IM electron.exe /T
    taskkill /F /IM node.exe /T
    # (Ignora si dice "no se encontró el proceso")

    # Si usas CMD (Símbolo de sistema antiguo):
    # rmdir /s /q dist
    # rmdir /s /q dist-electron
    # rmdir /s /q dist-release
    ```
4.  Ejecuta el comando de construcción:
    ```powershell
    npm run build
    ```

## 3. Solución de Problemas Comunes

### Error: "Operation not permitted" o "EBUSY"
*   **Causa:** Tu Antivirus (Windows Defender, McAfee, etc.) está bloqueando la compresión del `.exe` o el archivo está abierto.
*   **Solución:**
    1.  Desactiva temporalmente el "Escudo de tiempo real".
    2.  O agrega la carpeta `Sistema Tenis` a las **Exclusiones** de tu antivirus.
    3.  Intenta de nuevo los pasos del punto 2.

### Error: "Github Runner"
Ignora esto. Es un problema de la nube de GitHub, no afecta tu construcción local.

## 4. Resultado
Si todo sale bien, encontrarás tu instalador en:
`c:\Users\benja\OneDrive\Escritorio\Sistema Tenis\desktop\dist-release\EdgeSet-Setup-0.0.0.exe`
