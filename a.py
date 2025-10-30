#!/usr/bin/env python3
"""
capture_esp32.py

Descargas:
  - Una captura única desde la ESP32 (GET http://<IP>/capture) y la guarda como 'captura.jpg'.
  - Opcionalmente muestra el stream MJPEG (http://<IP>/stream) en una ventana OpenCV.

Uso:
  # Descargar una foto y guardar:
  python capture_esp32.py --ip 192.168.1.86

  # Mostrar video en tiempo real (presiona 'q' para salir):
  python capture_esp32.py --ip 192.168.1.86 --stream

Requisitos:
  pip install requests opencv-python numpy
"""

import argparse
import sys
import time

import requests
import cv2
import numpy as np


def download_capture(ip: str, out_file: str = "captura.jpg", timeout: int = 10) -> bool:
    """
    Descarga una única imagen desde el endpoint /capture y la guarda en disco.
    Devuelve True si tuvo éxito.
    """
    url = f"http://{ip}/capture"
    print(f"[+] Descargando imagen desde: {url}")
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] Error al descargar captura: {e}")
        return False

    # Guardar contenido binario
    try:
        with open(out_file, "wb") as f:
            f.write(resp.content)
        print(f"[+] Guardado en: {out_file}")
        return True
    except Exception as e:
        print(f"[!] Error al guardar archivo: {e}")
        return False


def show_stream_opencv(ip: str, mjpeg_path: str = "/stream"):
    """
    Intenta abrir el stream MJPEG con OpenCV VideoCapture. Si eso falla, 
    hace lectura en crudo con requests y decodifica JPEGs parciales.
    Presiona 'q' para salir.
    """
    url = f"http://{ip}{mjpeg_path}"
    print(f"[+] Intentando abrir stream con OpenCV: {url}")
    cap = cv2.VideoCapture(url)

    # Si VideoCapture funciona normalmente
    if cap.isOpened():
        print("[+] OpenCV VideoCapture abierto. Presiona 'q' para salir.")
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                # pausa breve y reintento
                time.sleep(0.1)
                continue
            cv2.imshow("ESP32 Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()
        return

    # Si VideoCapture no abrió, usar parser de MJPEG con requests
    print("[i] OpenCV VideoCapture no funcionó. Intentando leer MJPEG con requests...")
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code != 200:
            print(f"[!] Error HTTP al abrir stream: {r.status_code}")
            return
        bytes_buf = bytes()
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                bytes_buf += chunk
                a = bytes_buf.find(b"\xff\xd8")  # start JPEG
                b = bytes_buf.find(b"\xff\xd9")  # end JPEG
                if a != -1 and b != -1 and b > a:
                    jpg = bytes_buf[a : b + 2]
                    bytes_buf = bytes_buf[b + 2 :]
                    # decodificar JPEG a imagen numpy
                    nparr = np.frombuffer(jpg, dtype=np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("ESP32 Stream (requests MJPEG)", frame)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"[!] Error al leer stream MJPEG: {e}")


def main():
    parser = argparse.ArgumentParser(description="Descargar/capturar/mostrar stream desde ESP32-S3-CAM")
    parser.add_argument("--ip", required=True, help="IP del dispositivo ESP32 (ej. 192.168.1.86)")
    parser.add_argument("--out", default="captura.jpg", help="Nombre de archivo para la captura (por defecto captura.jpg)")
    parser.add_argument("--stream", action="store_true", help="Mostrar el stream en tiempo real con OpenCV")
    args = parser.parse_args()

    ip = args.ip

    # Intentar descargar una sola captura
    ok = download_capture(ip, out_file=args.out)
    if not ok:
        print("[!] No se pudo descargar la captura. Aún así puedes intentar abrir el stream (si --stream).")

    # Si el usuario pidió ver stream, abrirlo
    if args.stream:
        show_stream_opencv(ip)


if __name__ == "__main__":
    main()


"""Instrucciones rápidas

Instalar dependencias (en Windows cmd):

Nota: en algunos sistemas Windows, opencv-python puede necesitar ruedas precompiladas; si tienes problemas, prueba pip install opencv-python-headless (sin GUI) y usa un entorno que soporte mostrar ventanas (normalmente el paquete normal funciona).

Ejecutar (ejemplo):

Descargar una foto:
Descargar y ver stream en tiempo real:
Cambiar nombre de archivo:
Notas y recomendaciones

Endpoints:
Usamos /capture para una sola foto y /stream para el MJPEG. Si tu firmware usa otros endpoints, ajusta la ruta.
Si el stream no se muestra con VideoCapture, el script cae al parser MJPEG implementado con requests (más lento pero más fiable para flujos MJPEG simples).
Si tu ESP32 está en otra subred (por ejemplo AP del dispositivo), conecta tu PC al AP del ESP32 antes de ejecutar el script.
Para mejorar robustez, se pueden añadir reintentos, autenticación (si la hubieras añadido) y soporte para HTTPS si aplica."""