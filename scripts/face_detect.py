#!/usr/bin/env python3
"""
Face detection client for ESP32 CameraWebServer

Usage:
  python scripts/face_detect.py --ip 192.168.4.1

This script connects to the camera MJPEG stream (default /stream) and runs a
DNN-based face detector (ResNet SSD from OpenCV). If the model files are not
present, it downloads them automatically into the local `models/` folder.

Requirements:
    pip install opencv-python numpy requests
    # Optional (MQTT publishing): pip install paho-mqtt

Notes:
  - Press 'q' to quit, 's' to save the current frame to the output folder.
  - Use --capture to fetch a single /capture snapshot and run detection on it.
"""

import os
import sys
import time
import argparse
import pathlib
import urllib.request

import cv2
import numpy as np
import json

# MQTT helper (optional)
try:
    from mqtt_helper import MqttPublisher
except Exception:
    MqttPublisher = None


MODEL_DIR = pathlib.Path(__file__).resolve().parent / "models"
PROTOTXT_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
# Primary model URL (may move). We'll try a fallback if this 404s.
MODEL_URL = "https://github.com/opencv/opencv_3rdparty/raw/master/res10_300x300_ssd_iter_140000.caffemodel"
# Alternative candidate (raw usercontent on opencv repo sample path)
MODEL_URL_ALT = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/res10_300x300_ssd_iter_140000.caffemodel"
PROTOTXT_NAME = "deploy.prototxt"
MODEL_NAME = "res10_300x300_ssd_iter_140000.caffemodel"


def ensure_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    proto = MODEL_DIR / PROTOTXT_NAME
    model = MODEL_DIR / MODEL_NAME
    if not proto.exists():
        print(f"Descargando prototxt desde {PROTOTXT_URL}...")
        urllib.request.urlretrieve(PROTOTXT_URL, str(proto))
    if not model.exists():
        # Try primary URL first, fall back to alternative, otherwise print manual instructions
        tried = []
        def try_download(url):
            print(f"Descargando modelo Caffe desde {url} (puede tardar)...")
            tried.append(url)
            urllib.request.urlretrieve(url, str(model))

        import urllib.error
        try:
            try_download(MODEL_URL)
        except urllib.error.HTTPError as he:
            print(f"Error descargando desde primary URL: {he}. Intentando URL alternativa...")
            try:
                try_download(MODEL_URL_ALT)
            except Exception as e:
                print(f"Fallo en las descargas automáticas: {e}")
                print("\nPor favor descarga manualmente el archivo 'res10_300x300_ssd_iter_140000.caffemodel' y colócalo en:")
                print(f"  {model}")
                print("Puedes descargarlo desde un mirror o buscar 'res10_300x300_ssd_iter_140000.caffemodel' en GitHub y usar el enlace 'Raw'.")
                print("Ejemplos (desde tu máquina local):")
                print("  curl -L -o res10_300x300_ssd_iter_140000.caffemodel https://<raw-url-to-file>")
                print(f"  mv res10_300x300_ssd_iter_140000.caffemodel \"{model}\"")
                raise
        except Exception as e:
            # generic fallback message
            print(f"Fallo descargando el modelo: {e}")
            print("Intenta descargar manualmente y colocar el archivo en el directorio 'models/'.")
            raise
    return str(proto), str(model)


def detect_on_frame(net, frame, conf_threshold=0.5):
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                 (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    faces = []
    for i in range(0, detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence > conf_threshold:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype('int')
            # clip
            startX, startY = max(0, startX), max(0, startY)
            endX, endY = min(w - 1, endX), min(h - 1, endY)
            faces.append((startX, startY, endX, endY, confidence))
    return faces


def run_stream(args):
    use_haar = False
    try:
        proto, model = ensure_model()
        print("Cargando red DNN...")
        net = cv2.dnn.readNetFromCaffe(proto, model)
    except Exception:
        print("No se pudo usar el detector DNN. Se usará un clasificador Haar cascade como fallback (menos preciso).")
        net = None
        use_haar = True
        haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(haar_path):
            print("No se encontró el archivo Haar cascade en la instalación de OpenCV:", haar_path)
            print("Puedes instalar un paquete de datos o descargar 'haarcascade_frontalface_default.xml' y colocar en el directorio 'models/'.")
        else:
            haar = cv2.CascadeClassifier(haar_path)
    
    # Optional MQTT client (clean wrapper)
    mqtt_client = None
    if args.mqtt_host:
        if MqttPublisher is None:
            print("mqtt_helper no disponible o paho-mqtt no instalado. Instala: pip install paho-mqtt")
        else:
            try:
                mqtt_client = MqttPublisher(args.mqtt_host, port=args.mqtt_port, topic=args.mqtt_topic,
                                             user=args.mqtt_user, password=args.mqtt_pass)
                mqtt_client.connect()
                mqtt_client.loop_start()
                print(f"Conectado a MQTT broker {args.mqtt_host}:{args.mqtt_port}")
            except Exception as e:
                print("No se pudo conectar al broker MQTT:", e)
                mqtt_client = None
    url = f"http://{args.ip}{args.endpoint}"
    print(f"Conectando a stream: {url}")
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("No se pudo abrir el stream con OpenCV. Intenta usar --capture o verifica la IP/endpoints.")
        return

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    frame_idx = 0
    t0 = time.time()
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Error leyendo frame (stream terminó o fallo). Reintentando en 1s...")
            time.sleep(1)
            continue

        if use_haar:
            # Haar returns rectangles (x, y, w, h)
            rects = haar.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), scaleFactor=1.1, minNeighbors=5,
                                           minSize=(30, 30))
            faces = [(int(x), int(y), int(x + w), int(y + h), 0.5) for (x, y, w, h) in rects]
        else:
            faces = detect_on_frame(net, frame, args.confidence)
        # dibujar cajas
        for (sx, sy, ex, ey, conf) in faces:
            label = f"{conf*100:.1f}%"
            cv2.rectangle(frame, (sx, sy), (ex, ey), (0, 255, 0), 2)
            y = sy - 10 if sy - 10 > 10 else sy + 10
            cv2.putText(frame, label, (sx, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

        # mostrar FPS simple
        frame_idx += 1
        if frame_idx % 10 == 0:
            t1 = time.time()
            fps = 10.0 / (t1 - t0 + 1e-6)
            t0 = t1
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Face Detection", frame)
        # Publish detections via MQTT if enabled
        if mqtt_client and faces:
            payload = {
                "timestamp": time.time(),
                "source": args.ip,
                "frame": frame_idx,
                "faces": [
                    {"x1": int(sx), "y1": int(sy), "x2": int(ex), "y2": int(ey), "confidence": float(conf)}
                    for (sx, sy, ex, ey, conf) in faces
                ]
            }
            try:
                mqtt_client.publish(payload)
            except Exception as e:
                print("Error publicando en MQTT:", e)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('s'):
            fname = outdir / f"frame_{int(time.time())}.jpg"
            cv2.imwrite(str(fname), frame)
            print("Guardado:", fname)

    cap.release()
    cv2.destroyAllWindows()
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        except Exception:
            pass


def run_capture(args):
    # captura única desde /capture
    import requests
    url = f"http://{args.ip}/capture"
    print("Solicitando snapshot...", url)
    r = requests.get(url, stream=True, timeout=10)
    r.raise_for_status()
    data = r.content
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        print("No se pudo decodificar la imagen devuelta por /capture")
        return

    try:
        proto, model = ensure_model()
        net = cv2.dnn.readNetFromCaffe(proto, model)
        faces = detect_on_frame(net, frame, args.confidence)
    except Exception:
        print("No se pudo usar el detector DNN. Se usará Haar cascade como fallback (menos preciso).")
        haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(haar_path):
            haar = cv2.CascadeClassifier(haar_path)
            rects = haar.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), scaleFactor=1.1, minNeighbors=5,
                                           minSize=(30, 30))
            faces = [(int(x), int(y), int(x + w), int(y + h), 0.5) for (x, y, w, h) in rects]
        else:
            print("No se encontró Haar cascade en la instalación de OpenCV. Descarga 'haarcascade_frontalface_default.xml' o instala una versión de OpenCV con datos.")
            faces = []
    for (sx, sy, ex, ey, conf) in faces:
        cv2.rectangle(frame, (sx, sy), (ex, ey), (0, 255, 0), 2)
        cv2.putText(frame, f"{conf*100:.1f}%", (sx, sy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / f"capture_{int(time.time())}.jpg"
    cv2.imwrite(str(fname), frame)
    print("Guardado:", fname)
    cv2.imshow("Capture", frame)
    print("Presiona cualquier tecla en la ventana para cerrar...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # Optional MQTT publish for capture (using mqtt_helper)
    if args.mqtt_host:
        if MqttPublisher is None:
            print("mqtt_helper no disponible o paho-mqtt no instalado. Instala: pip install paho-mqtt")
        else:
            try:
                pub = MqttPublisher(args.mqtt_host, port=args.mqtt_port, topic=args.mqtt_topic,
                                    user=args.mqtt_user, password=args.mqtt_pass)
                pub.connect()
                payload = {
                    "timestamp": time.time(),
                    "source": args.ip,
                    "frame": fname.name,
                    "faces": [
                        {"x1": int(sx), "y1": int(sy), "x2": int(ex), "y2": int(ey), "confidence": float(conf)}
                        for (sx, sy, ex, ey, conf) in faces
                    ]
                }
                pub.publish(payload)
                pub.disconnect()
                print("Publicadas detecciones al broker MQTT")
            except Exception as e:
                print("Error publicando en MQTT:", e)


def parse_args():
    p = argparse.ArgumentParser(description="Face detection client for ESP32 CameraWebServer")
    p.add_argument('--ip', required=True, help='IP address of the camera (e.g. 192.168.4.1)')
    p.add_argument('--endpoint', default='/stream', help='Endpoint to use (default /stream)')
    p.add_argument('--capture', action='store_true', help='Use single /capture request instead of MJPEG stream')
    p.add_argument('--outdir', default='captures', help='Directory to save snapshots/frames')
    p.add_argument('--confidence', type=float, default=0.5, help='Minimum confidence for detections')
    # MQTT options (optional). If --mqtt-host is provided the script will attempt
    # to connect and publish detection events to the given topic.
    p.add_argument('--mqtt-host', help='MQTT broker hostname or IP (optional)')
    p.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port (default 1883)')
    p.add_argument('--mqtt-topic', default='camera/detections', help='MQTT topic to publish detections')
    p.add_argument('--mqtt-user', help='MQTT username (optional)')
    p.add_argument('--mqtt-pass', help='MQTT password (optional)')
    return p.parse_args()


def main():
    args = parse_args()
    try:
        if args.capture:
            run_capture(args)
        else:
            run_stream(args)
    except KeyboardInterrupt:
        print('\nInterrumpido por el usuario')
    except Exception as e:
        print('Error:', e)


if __name__ == '__main__':
    main()
