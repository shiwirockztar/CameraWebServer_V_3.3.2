# Face Detection - Uso y configuración

Este README explica cómo instalar dependencias y ejecutar el script de detección de rostros
`scripts/face_detect.py` incluido en este repositorio.

Resumen rápido
- Script principal: `scripts/face_detect.py`
- Script auxiliar MQTT (opcional): `scripts/mqtt_helper.py`
- Modelos descargados automáticamente en: `scripts/models/`
- Requisitos mínimos: Python 3.8+

1) Crear un entorno virtual (recomendado)

Windows (cmd.exe):

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

Linux / macOS (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Instalar dependencias

Hay un `requirements.txt` mínimo en la misma carpeta. Puedes instalarlo así:

```bash
pip install -r scripts/requirements.txt
```

Contenido principal (si instalas manualmente):
- opencv-python  -> lectura y DNN para detección
- numpy
- requests      -> para descargar snapshots (/capture)
- paho-mqtt     -> opcional para publicar resultados vía MQTT (si lo vas a usar)

Si instalas manualmente:

```bash
pip install opencv-python numpy requests paho-mqtt
```

Nota: `opencv-python` incluye binarios para la mayoría de plataformas. En Windows si `VideoCapture` no abre el MJPEG stream correctamente, usa la opción `--capture` para tomar un snapshot con `/capture` y procesarlo (el script soporta ambos modos).

3) Ejecutar el script

- Detección en tiempo real (stream MJPEG):

```bash
python scripts/face_detect.py --ip 192.168.4.1
```

- Captura única (snapshot /capture, útil si `VideoCapture` no funciona):

```bash
python scripts/face_detect.py --ip 192.168.4.1 --capture
```

- Publicar detecciones vía MQTT (opcional):

```bash
python scripts/face_detect.py --ip 192.168.4.1 --mqtt-host test.mosquitto.org --mqtt-topic camera/detections
```

Con autenticación MQTT:

```bash
python scripts/face_detect.py --ip 192.168.4.1 --mqtt-host mi.broker.local --mqtt-user usuario --mqtt-pass clave
```
Ejemplos: ejecutar desde la raíz vs desde dentro de `scripts`
--------------------------------------------------------

Problema común: si estás dentro de la carpeta `scripts` y ejecutas
`python scripts\face_detect.py ...`, Python buscará `scripts/scripts/face_detect.py`
(ruta duplicada) y fallará con "No such file or directory".

Usa uno de estos patrones según tu directorio actual:

- Desde la raíz del repositorio (una carpeta arriba de `scripts`):

```cmd
python scripts\face_detect.py --ip 192.168.4.1
```

- Desde dentro de la carpeta `scripts` (has hecho `cd scripts`):

```cmd
python face_detect.py --ip 192.168.4.1
```

- Ruta absoluta (funciona desde cualquier directorio):

```cmd
python "C:\\Users\\SHIIWITOCKZRAT\\Documents\\Arduino\\CameraWebServer_v_3_3_2\\scripts\\face_detect.py" --ip 192.168.4.1
```

Antes de ejecutar, comprueba tu directorio actual con `echo %cd%` (cmd.exe)
o `pwd` (bash) para elegir la forma correcta.

Argumentos útiles
- `--ip` (obligatorio): IP de la cámara (ej: `192.168.4.1`).
- `--endpoint`: endpoint HTTP (por defecto `/stream`). Cambia a `/capture` si lo prefieres.
- `--capture`: pide un único snapshot y ejecuta detección sobre él.
- `--outdir`: carpeta para guardar capturas y frames (por defecto `captures`).
- `--confidence`: umbral de confianza para detecciones (0..1, defecto 0.5).
- `--mqtt-host`, `--mqtt-port`, `--mqtt-topic`, `--mqtt-user`, `--mqtt-pass`: opciones de broker MQTT.

Formato de las publicaciones MQTT
- Cada mensaje es un JSON con este esquema:

```json
{
  "timestamp": 1698661234.123,
  "source": "192.168.4.1",
  "frame": 123,
  "faces": [
    {"x1": 10, "y1": 20, "x2": 110, "y2": 140, "confidence": 0.96}
  ]
}
```

Pruebas y verificación MQTT
- Usando mosquitto (cliente):

```bash
mosquitto_sub -h test.mosquitto.org -t camera/detections -v
```

- Pequeño suscriptor Python:

```python
import paho.mqtt.client as mqtt

def on_message(c, u, msg):
    print(msg.topic, msg.payload.decode())

c = mqtt.Client()
c.on_message = on_message
c.connect('test.mosquitto.org', 1883)
c.subscribe('camera/detections')
c.loop_forever()
```

Modelos (descarga automática)
- Al ejecutar el script por primera vez, los archivos del detector (deploy.prototxt y
  res10_300x300_ssd_iter_140000.caffemodel) se descargarán en `scripts/models/`.
- Si quieres predescargar los archivos o verificarlos manualmente, puedes colocar ahí
  `deploy.prototxt` y `res10_300x300_ssd_iter_140000.caffemodel`.

Problemas comunes y soluciones
- VideoCapture no abre el stream en Windows:
  - Prueba la opción `--capture` (usa /capture en lugar de /stream).
  - Asegúrate de que la cámara sirve MJPEG en `/stream` (algunas builds sirven Motion JPEG).
- El script tarda en arrancar la primera vez: está descargando el modelo (archivo grande).
- Si el MQTT no publica, revisa que el broker acepte conexiones no TLS o configura usuario/contraseña.

Mejoras posibles (siguientes pasos)
- Añadir TLS y QoS en `mqtt_helper.py` para producción segura.
- Guardado automático de recortes de caras y subida a almacenamiento seguro.
- Detectar "nuevas" caras (debounce) para reducir cantidad de mensajes MQTT.

Contacto rápido
- Si quieres que adapte el script a un broker MQTT específico (TLS, credenciales, tópico, QoS), pásame los requisitos y lo adapto.

---
Generado por el asistente para facilitar ejecución del script en este repo.

Usar desde GitHub Codespaces / Dev Container
-----------------------------------------

Aquí tienes instrucciones y recomendaciones si vas a ejecutar los scripts dentro de un entorno tipo GitHub Codespaces o un devcontainer de VS Code.

1) Distinción importante
- Codespaces en la nube (GitHub Codespaces): el contenedor se ejecuta en la infraestructura de GitHub (remota). Desde ahí, por defecto, no podrás acceder directamente a dispositivos que estén en tu red local (por ejemplo, la IP `192.168.x.x` de la cámara) porque el contenedor no comparte la misma LAN que tu máquina.
- Devcontainer local (Remote - Containers / Docker en tu máquina): el contenedor se ejecuta en tu equipo y sí tiene acceso a la red local de la máquina host (salvo restricciones de red/Firewall). Para trabajar con la cámara localmente esta opción es normalmente la más simple.

2) Recomendaciones según el caso
- Si usas Codespaces en la nube y necesitas acceder a la cámara local:
  - Opción A: Ejecutar el script en tu máquina local (fuera de Codespaces). Esto evita problemas de red.
  - Opción B: Exponer la cámara a Internet (NO recomendado sin medidas de seguridad) o usar un túnel seguro como `ngrok` o configurar la cámara para que publique eventos a un broker MQTT público/privado accesible desde la nube.
  - Opción C: usar un broker MQTT accesible desde la nube y configurar la cámara (firmware) para publicar detecciones al broker; el script en Codespaces se suscribe al tópico.

- Si usas el devcontainer local (o ejecutas Codespaces/Containers en tu ordenador): el contenedor tendrá visibilidad de la red local y puedes usar la IP de la cámara directamente (ej: `192.168.4.1`).

3) Pasos rápidos en un Codespace/devcontainer (local o remoto)

- Abrir el repositorio en Codespaces o abrir la carpeta con Remote - Containers.
- Asegúrate de tener Python 3.8+ en el contenedor (el devcontainer del repo debería incluirlo o puedes instalarlo con el Dockerfile/container image).
- Crear y activar un virtualenv dentro del contenedor (recomendado):

Windows (cmd.exe dentro del contenedor/terminal):

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

Linux / macOS (bash dentro del contenedor):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Instalar dependencias:

```bash
pip install -r scripts/requirements.txt
```

- Ejecutar el script (ejemplo con snapshot):

```bash
python scripts/face_detect.py --ip 192.168.4.1 --capture --outdir out
```

o para stream:

```bash
python scripts/face_detect.py --ip 192.168.4.1 --endpoint /stream
```

Nota sobre la IP: si tu contenedor está en la nube, `192.168.4.1` no será accesible desde allí; en ese caso usa una de las opciones descritas arriba (broker MQTT, túnel, o ejecutar localmente).

4) Opciones útiles para Codespaces remotos
- Usar MQTT como puente: hace que la cámara y el procesador de detecciones (script) no necesiten estar en la misma red. Configura un broker (p. ej. CloudMQTT, Mosquitto en VPS o un broker gestionado) y usa `--mqtt-host` en el script.
- Subida de imágenes a almacenamiento en la nube: en vez de acceder directamente a la cámara, haz que la cámara suba snapshots a un endpoint o almacenamiento y procesa desde ahí.

5) Diagnóstico rápido
- Si `requests` a `http://<IP>/capture` falla con timeout desde Codespaces remoto, es por conectividad de red (no por el script). Prueba a ejecutar `curl http://<IP>/capture` desde tu máquina local para confirmar.
- Para debugging en Codespaces remoto, considera hacer una prueba simples usando `curl` o `ping` desde el terminal del contenedor para verificar qué hosts son accesibles.

Si quieres, puedo añadir ejemplos concretos para conectar el script a un broker MQTT en la nube (con TLS/usuario) o un ejemplo de configuración de `ngrok` para exponer temporalmente la cámara de forma segura. ¿Cuál de las opciones prefieres que documente/añada?
