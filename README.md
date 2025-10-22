# CameraWebServer (PlatformIO)

Proyecto convertido para usar con PlatformIO (ESP32 - Arduino framework).

Pasos rápidos:

1. Instala PlatformIO en VS Code o la CLI de PlatformIO.
2. Abre esta carpeta en VS Code.
3. Ajusta las credenciales WiFi en `src/main.cpp` (ssid / password).
4. Si usas otra placa, edita `platformio.ini` y cambia `board` al id correcto.
5. Compila y sube desde la interfaz de PlatformIO o con la CLI:

   pio run
   pio run -t upload

Notas:

- Los fuentes originales se copiaron a `src/` para que PlatformIO los compile.
- `board_config.h` selecciona `CAMERA_MODEL_ESP32S3_EYE` por defecto; cámbialo si usas otra placa.
- Si necesitas particiones o flags especiales (PSRAM/partitions), ajusta `platformio.ini`.

## Git quick-recovery commands

Si necesitas restaurar tu copia de trabajo al último commit limpio o eliminar los archivos no rastreados, usa estos comandos desde la raíz del proyecto (cmd.exe / PowerShell):

```bash
git restore .        # Restaura todos los archivos modificados
git clean -fd        # Elimina archivos/directorios no rastreados
```

Usa con cuidado: `git clean -fd` eliminará archivos no rastreados permanentemente (es recomendable revisar con `git clean -n` primero).
