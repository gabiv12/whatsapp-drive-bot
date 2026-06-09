# WhatsApp Drive Bot

MVP simulado para recibir archivos por WhatsApp, elegir una persona, elegir una carpeta y simular el guardado en Google Drive.

Por ahora no descarga media real desde Twilio, no usa Twilio SDK para enviar mensajes salientes y no conecta Google Drive real. El sistema está centrado en estas personas:

- `fernando_gutman`: Fernando Gutman
- `pablo_sanchez`: Pablo Sanchez

## Instalación

Abrir PowerShell y entrar al proyecto:

```powershell
cd D:\Desktop\KANI\whatsapp-drive-bot
```

Crear el entorno virtual:

```powershell
python -m venv venv
```

Activarlo:

```powershell
.\venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Copiar variables de entorno:

```powershell
copy .env.example .env
```

## Levantar El Servidor

El comando correcto es:

```powershell
cd D:\Desktop\KANI\whatsapp-drive-bot
python -m uvicorn app.main:app --reload
```

Si aparece este error:

```text
ModuleNotFoundError: No module named 'app'
```

significa que Uvicorn se está ejecutando desde una carpeta incorrecta. Hay que ejecutarlo desde:

```text
D:\Desktop\KANI\whatsapp-drive-bot
```

## Códigos Internos Y Nombres Visibles

Cada carpeta tiene un código interno estable y un nombre visible editable.

Ejemplo:

```json
{
  "code": "C 011",
  "option": "11",
  "name": "Facturas carbon enero",
  "description": "Facturas cargadas en enero",
  "drive_folder_id": ""
}
```

`C 011` es el identificador interno de la carpeta dentro del catálogo local. `Facturas carbon enero` es el nombre visible que el usuario puede ir cambiando.

Renombrar una carpeta no crea otra carpeta. Solo cambia `name` y, si se envía, `description`. No cambia `code`, `option` ni `drive_folder_id`.

Crear carpeta sí crea un registro nuevo con el siguiente código disponible. Si una persona tiene `C 001` a `C 010`, la próxima carpeta será `C 011`.

Más adelante, `drive_folder_id` será el vínculo con Google Drive real. Al renombrar, el sistema deberá cambiar el nombre en Drive manteniendo el mismo ID.

Cuando el bot muestra carpetas, usa este formato:

```text
1. C 001
11. C 011 - Facturas carbon enero
```

Si `name` es igual a `code`, muestra solo el código. Si `name` es distinto, muestra `code - name`.

## Sincronización Con La PC Del Cliente

No hace falta desarrollar una app de escritorio propia para la PC del cliente.

La sincronización futura se apoyará en Google Drive para escritorio:

```text
WhatsApp -> Bot -> Google Drive -> Google Drive para escritorio -> PC del cliente
```

El bot subirá los archivos a Google Drive. La PC del cliente tendrá instalado Google Drive para escritorio, que se encargará de sincronizar esos archivos automáticamente.

Si el cliente necesita abrir archivos aunque no tenga conexión en ese momento, se podrá marcar la carpeta como disponible sin conexión desde Google Drive para escritorio.

Si el cliente cambia nombres manualmente desde la PC o desde Drive, más adelante habrá que definir cómo se sincronizan esos cambios con el catálogo local del bot.

## Pruebas JSON Locales

Probar estado:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get
```

Resetear conversaciones y archivos pendientes:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/debug/reset" -Method Post
```

Enviar archivos:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/webhook/whatsapp" -Method Post -ContentType "application/json" -Body '{"user_id":"whatsapp:+5491111111111","text":"","media_count":3,"media_names":["factura_001.pdf","remito_001.pdf","comprobante_001.jpg"]}'
```

Elegir Fernando Gutman:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/webhook/whatsapp" -Method Post -ContentType "application/json" -Body '{"user_id":"whatsapp:+5491111111111","text":"1"}'
```

Elegir carpeta:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/webhook/whatsapp" -Method Post -ContentType "application/json" -Body '{"user_id":"whatsapp:+5491111111111","text":"C001"}'
```

La respuesta final debe incluir:

```text
Listo. Guardé 3 archivo/s en Fernando Gutman / C 001.
```

## Comando Rápido Por WhatsApp

El usuario puede enviar un archivo y escribir persona + carpeta en el mismo mensaje. Si el bot puede resolver ambos datos, guarda directo sin hacer preguntas intermedias.

Ejemplos:

```text
pablo C001
fernando C010
gutman facturas carbon enero
```

Si el texto incluye solo la persona, por ejemplo `pablo`, el bot guarda los archivos pendientes y muestra las carpetas de Pablo Sanchez.

Si el texto incluye solo la carpeta, por ejemplo `C001`, el bot guarda esa carpeta como sugerencia, pregunta la persona y después intenta guardar directo con esa persona.

Si la carpeta es ambigua, el bot no guarda y pide elegir una opción.

Prueba rápida local:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/debug/reset" -Method Post
Invoke-RestMethod -Uri "http://127.0.0.1:8000/webhook/whatsapp" -Method Post -ContentType "application/json" -Body '{"user_id":"whatsapp:+5491111111111","text":"pablo C001","media_count":1,"media_names":["factura_001.pdf"]}'
```

Respuesta esperada:

```text
Listo. Guardé 1 archivo/s en Pablo Sanchez / C 001.
```

## Personas Y Carpetas

Listar personas:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/persons" -Method Get
```

Listar carpetas de una persona:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/folders/fernando_gutman" -Method Get
```

Crear carpeta:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/folders/fernando_gutman" -Method Post -ContentType "application/json" -Body '{"name":"C 011","description":"Carpeta temporal"}'
```

Renombrar carpeta:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/folders/fernando_gutman/C011/rename" -Method Put -ContentType "application/json" -Body '{"name":"Facturas carbon enero","description":"Facturas cargadas en enero"}'
```

## Twilio Sandbox

En desarrollo local:

```powershell
python -m uvicorn app.main:app --reload
ngrok http 8000
```

En Twilio Console, ir a WhatsApp Sandbox y configurar `When a message comes in` con:

```text
https://TU-SUBDOMINIO.ngrok-free.app/webhook/twilio-debug
```

Método: `POST`.

`/webhook/twilio-debug` acepta `application/x-www-form-urlencoded` y devuelve XML/TwiML para que Twilio pueda mostrar la respuesta dentro de WhatsApp.

Prueba local TwiML:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/webhook/twilio-debug" -Method Post -ContentType "application/x-www-form-urlencoded" -Body "From=whatsapp:%2B5493644647451&Body=pablo%20C001&NumMedia=1&MediaContentType0=application%2Fpdf&MediaUrl0=https%3A%2F%2Fapi.twilio.com%2Ffake"
```

`/webhook/whatsapp` sigue devolviendo JSON para pruebas locales con `Invoke-RestMethod`.

`/webhook/twilio-json-debug` queda disponible para inspeccionar payloads de Twilio en JSON, pero no debe usarse como URL del Sandbox si se quiere responder dentro de WhatsApp.

## Deploy En Render

1. Crear un repositorio en GitHub.
2. Subir este proyecto al repositorio.
3. En Render, crear un nuevo `Web Service`.
4. Conectar Render con el repositorio de GitHub.
5. Configurar:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

El archivo `render.yaml` ya usa ese comando de inicio.

Variables de entorno necesarias en Render:

```text
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
GOOGLE_CLIENT_EMAIL=
GOOGLE_PRIVATE_KEY=
GOOGLE_DRIVE_ROOT_FOLDER_ID=
APP_ENV=production
ALLOWED_OWNER_NUMBERS=
```

No cargar credenciales reales en el código ni en GitHub.

Cuando Render termine el deploy, se obtiene una URL pública similar a:

```text
https://whatsapp-drive-bot.onrender.com
```

Configurar Twilio Sandbox:

```text
When a message comes in:
https://URL-RENDER/webhook/twilio-debug

Method:
POST
```

Luego probar desde WhatsApp:

```text
hola
pablo C001
fernando C001
```

## Subir A GitHub

Desde la carpeta del proyecto:

```powershell
cd D:\Desktop\KANI\whatsapp-drive-bot
git init
git add .
git commit -m "Cerrar MVP WhatsApp Drive Bot"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/whatsapp-drive-bot.git
git push -u origin main
```

Antes de hacer `git add .`, verificar que `.env`, credenciales y logs no estén incluidos. `.gitignore` ya excluye esos archivos.

## Próxima Etapa Google Drive

Ver [docs/google-drive-setup.md](docs/google-drive-setup.md).

El objetivo será crear la carpeta raíz `Documentos Kani`, guardar su ID en `GOOGLE_DRIVE_ROOT_FOLDER_ID` y empezar a mapear `drive_folder_id` en `data/folders.json`.
