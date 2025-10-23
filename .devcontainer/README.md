to use a pre-built image with PlatformIO, replace `image` with a PlatformIO-ready image or add a
# Devcontainer para CameraWebServer_v_3.3.2

Este archivo está en la carpeta `.devcontainer` y documenta cómo está configurado el
entorno de desarrollo para usar en GitHub Codespaces o Dev Containers.

Proporciona una imagen base Debian ligera y prepara PlatformIO vía `postCreateCommand`.

## Extensiones añadidas y por qué

En `customizations.vscode.extensions` del `devcontainer.json` incluí las siguientes extensiones
con una breve explicación (todas están en el contenedor y se instalarán automáticamente al abrir):

- `marus25.cortex-debug`
  - Front-end de depuración para dispositivos Cortex-M. Útil si usas adaptadores SWD/JTAG.

- `ms-vscode.cpptools`
  - Soporte C/C++ de Microsoft: IntelliSense, navegación de código y utilidades de depuración.

- `espressif.esp-idf-extension`
  - Extensión oficial de ESP-IDF. Opcional para proyectos Arduino/PlatformIO, pero útil si trabajas
    con ESP-IDF nativo.

- `platformio.platformio-ide`
  - Integración de PlatformIO en VS Code: compilación, subida y depuración para placas como ESP32.

- `ms-python.python`
  - Soporte para Python; PlatformIO y scripts usan Python, y esta extensión habilita lint/entornos.

- `streetsidesoftware.code-spell-checker`
  - Corrector ortográfico ligero para comentarios y strings.

- `mhutchie.git-graph`
  - Visualiza el historial de git en forma de grafo.

- `eamodio.gitlens`
  - Añade anotaciones, blame y herramientas avanzadas para explorar el historial de git.

- `esbenp.prettier-vscode`
  - Formateador Prettier; se combina con `editor.formatOnSave` para formateo automático.

- `dbaeumer.vscode-eslint`
  - Integración ESLint para proyectos JavaScript/TypeScript.

## Ajustes aplicados en el devcontainer

Los ajustes se aplican dentro de `customizations.vscode.settings` y son:

- `editor.formatOnSave: true` — formatea los ficheros soportados al guardar.
- `C_Cpp.clang_format_fallbackStyle: Google` — estilo de formateo por defecto para C/C++.
- `python.linting.enabled: true` y `python.linting.pylintEnabled: true` — linting básico para Python.

## Cómo añadir las extensiones que usas localmente

Si quieres incluir exactamente las extensiones que tienes instaladas en tu VS Code local:

1. En tu máquina local ejecuta:

```bash
code --list-extensions
```

2. Copia la lista de IDs (cada línea es un ID de extensión) y pégalos en
   `customizations.vscode.extensions` dentro de `.devcontainer/devcontainer.json`.

Ejemplo de inserción:

```json
"customizations": {
  "vscode": {
    "extensions": [
      "platformio.platformio-ide",
      "ms-vscode.cpptools",
      "your.favorite.extension"
    ]
  }
}
```

## postCreateCommand

El `postCreateCommand` instala PlatformIO y dependencias (Python, compiladores básicos).
Si prefieres evitar la instalación en el `postCreateCommand`, se puede crear un `Dockerfile`
con PlatformIO ya instalado y usar la propiedad `build` en lugar de `image`.

## Notas y compatibilidad

- Algunos validadores de devcontainer pueden advertir sobre campos no estándar como
  `devcontainerNotes` o `description`. Esas claves se usan aquí sólo para dejar notas
  amigables dentro del JSON; puedes eliminarlas para cumplir estrictamente el esquema.
- Codespaces (remoto) no permite mapear USB locales de forma directa para subir a un
  dispositivo físico. Para programar placas físicamente conectadas, lo habitual es:
  - ejecutar PlatformIO localmente (fuera de Codespaces), o
  - montar una VM/host con acceso USB y hacer upload desde allí.

## ¿Qué más quieres que haga?

- Eliminar `devcontainerNotes` para validación estricta.
- Crear un `Dockerfile` que incluya PlatformIO ya instalado.
- Añadir un script helper para facilitar uploads locales si usas devcontainer en tu máquina.

Si quieres que haga alguno de estos cambios, dímelo y lo implemento.

---
Archivo actualizado en español.
