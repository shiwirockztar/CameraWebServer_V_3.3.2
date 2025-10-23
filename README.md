# CameraWebServer (PlatformIO)

Proyecto convertido para usar con PlatformIO (ESP32 - Arduino framework).

# CameraWebServer (PlatformIO)

Proyecto convertido para usar con PlatformIO (ESP32 - Arduino framework).

Pasos rápidos:

1. Instala PlatformIO en VS Code o la CLI de PlatformIO.
2. Abre esta carpeta en VS Code.
3. Ajusta las credenciales WiFi en `src/main.cpp` (o usa los comandos serie descritos abajo).
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

```
git restore .        # Restaura todos los archivos modificados
git clean -fd        # Elimina archivos/directorios no rastreados
```

Usa con cuidado: `git clean -fd` eliminará archivos no rastreados permanentemente (es recomendable revisar con `git clean -n` primero).

---

## Comandos serie (configuración Wi‑Fi)

El firmware incluye un pequeño intérprete de comandos por puerto serie que te permite ver y modificar las credenciales Wi‑Fi en tiempo de ejecución y guardarlas de forma persistente en la memoria NVS del ESP32.

Cómo usar:
- Abre el Monitor Serial con 115200 baudios (ej. en PlatformIO: "Monitor" o `pio device monitor -b 115200`).
- Escribe un comando y pulsa Enter. Los comandos son en texto plano y no distinguen entre mayúsculas/minúsculas para el nombre del comando.

Lista de comandos disponibles (detallada):

- help
   - Qué hace: muestra la lista de comandos y una breve ayuda.
   - Ejemplo: escribe `help` y pulsa Enter.

- setssid <ssid>
   - Qué hace: establece el SSID de la red Wi‑Fi a usar y lo guarda en NVS (persistente tras reinicios).
   - Ejemplo: `setssid MiRedCasa` -> respuesta: "SSID updated" y "Credentials saved to NVS".
   - Notas: no añade comillas; acepta espacios si los incluyes como parte del valor (mejor evitar espacios por simplicidad).

- setpass <password>
   - Qué hace: establece la contraseña Wi‑Fi y la guarda en NVS.
   - Ejemplo: `setpass MiClaveSecreta` -> respuesta: "Password updated" y "Credentials saved to NVS".
   - Notas: la contraseña se guarda en la memoria no volátil del dispositivo y no en el repositorio (no se sube a Git).

- show
   - Qué hace: muestra el SSID actual y una versión enmascarada de la contraseña (solo asteriscos) para evitar exponer la clave en el monitor.
   - Ejemplo: `show` -> salida: `SSID: MiRedCasa` y `Password: ********`.

- showip
   - Qué hace: muestra la IP actual si el dispositivo está conectado; si no lo está, imprime "Not connected to WiFi".
   - Ejemplo: `showip` -> `IP: 192.168.1.42` o `Not connected to WiFi`.

- connect
   - Qué hace: intenta conectar a la red Wi‑Fi usando las credenciales actualmente cargadas en memoria (las guardadas en NVS o los valores por defecto cargados desde `secrets/secrets.h`). Imprime puntos mientras intenta conectarse y finalmente el resultado (IP o fallo).
   - Ejemplo: `connect` -> `Connecting to WiFi 'MiRedCasa'...` seguido de `WiFi connected` y `IP: 192.168.1.42` (si tiene éxito) o `WiFi connection failed` si no.

- del
   - Qué hace: elimina las credenciales guardadas en NVS. Tras ejecutar este comando, al reiniciar (o al volver a ejecutar `loadCredentials()`), el dispositivo volverá a usar las credenciales por defecto que provienen de `secrets/secrets.h` o los valores de fallback (`YOUR_SSID`/`YOUR_PASSWORD`).
   - Ejemplo: `del` -> `Credentials removed from NVS`.

Consideraciones de seguridad:
- Las credenciales se almacenan en la memoria NVS del ESP32. No se suben al repositorio porque `secrets/secrets.h` está en `.gitignore` y las credenciales guardadas en NVS residen localmente en el dispositivo.
- Evita enviar contraseñas por canales inseguros o compartir tu monitor serial con personas no autorizadas.

Problemas comunes:
- Si la web muestra `http://0.0.0.0/`, normalmente significa que la ESP no tiene IP (no está conectada). Usa `showip` para verificar el estado y `connect` después de ajustar credenciales con `setssid`/`setpass`.
- Si `connect` falla repetidamente, revisa que la red esté en el rango y que el router no tenga el cliente bloqueado o aislamiento de clientes.

---

Si quieres, puedo añadir ejemplos rápidos de comandos a ejecutar desde PowerShell o la CLI para automatizar el envío (por ejemplo usando `echo "setssid MiRed" > COM3`), o bien puedo ejecutar una compilación para confirmar que todo compila correctamente.
