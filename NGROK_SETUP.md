# Exponer el backend con ngrok

Este proyecto usa WebSockets y HTTP en el puerto 8000 (backend FastAPI). Para que tu equipo pueda probar la aplicación sin compartir una IP pública fija, puedes abrir un túnel temporal con ngrok.

## Requisitos
- Cuenta gratuita de [ngrok](https://ngrok.com/) y token de autenticación.
- ngrok instalado localmente (descarga el binario y ponlo en tu `PATH`).
- Backend corriendo en tu máquina en el puerto `8000` y escuchando en todas las interfaces: `uvicorn app:app --host 0.0.0.0 --port 8000` desde la carpeta `backend/`.

## Configurar ngrok
1. **Autentica tu cliente** (una sola vez), reemplazando `TU_TOKEN` por el token de tu cuenta:
   ```bash
   ngrok config add-authtoken TU_TOKEN
   ```
2. **Abre el túnel HTTP al puerto 8000** (sirve tanto para HTTP como para WebSocket):
   ```bash
   ngrok http 8000
   ```

   Esto mostrará una URL pública similar a `https://<subdominio>.ngrok-free.app`.

## Usar la URL del túnel
- En el dashboard o en cualquier cliente, sustituye el host original por la URL de ngrok, manteniendo los endpoints:
  - WebSocket principal: `wss://<subdominio>.ngrok-free.app/ws`
  - Video admin: `wss://<subdominio>.ngrok-free.app/ws/admin/video`
  - Eventos admin: `wss://<subdominio>.ngrok-free.app/ws/admin/events`
- Si usas HTTP (por ejemplo, `GET /`), emplea `https://<subdominio>.ngrok-free.app/`.

## Buenas prácticas y seguridad
- **Cierra el túnel** cuando termines (Ctrl+C en la terminal de ngrok) para evitar que el puerto quede expuesto.
- No compartas el token de ngrok ni dejes servicios sensibles sin autenticación si decides exponerlos a Internet.
- En producción, añade autenticación a los endpoints WebSocket antes de exponerlos públicamente.

## Verificación rápida
1. Levanta el backend (puerto 8000).
2. Abre ngrok con `ngrok http 8000` y copia la URL `https` generada.
3. Desde otra máquina, abre el dashboard configurado para apuntar a esa URL; deberías ver los eventos si la red no bloquea salidas HTTPS.

