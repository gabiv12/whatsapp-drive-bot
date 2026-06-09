# Flujo WhatsApp

## Flujo Guiado

1. El usuario envía uno o varios archivos.
2. El bot guarda nombres de archivos pendientes en `data/pending_uploads.json`.
3. El bot pregunta para quién son:

```text
1. Fernando Gutman
2. Pablo Sanchez
```

4. El usuario elige la persona.
5. El bot muestra las carpetas de esa persona desde `data/folders.json`.
6. El usuario elige una carpeta por opción, código o nombre visible.
7. El sistema simula el guardado con `upload_to_drive(person_key, person_display_name, folder_data, files)`.
8. El bot limpia archivos pendientes, deja la conversación en `finished` y responde:

```text
Listo. Guardé X archivo/s en Fernando Gutman / C 001.
```

## Flujo Rápido

El usuario puede enviar archivo y comando en el mismo mensaje:

```text
pablo C001
fernando C010
gutman facturas carbon enero
```

Si el bot detecta persona y carpeta sin ambigüedad, guarda directo:

```text
Listo. Guardé 1 archivo/s en Pablo Sanchez / C 001.
```

Si el usuario envía archivo y solo persona, por ejemplo:

```text
pablo
```

el bot guarda los archivos pendientes, deja seleccionada la persona y muestra las carpetas de Pablo Sanchez.

Si el usuario envía archivo y solo carpeta, por ejemplo:

```text
C001
```

el bot guarda la carpeta como sugerencia, pregunta la persona y después intenta guardar directo con la persona elegida.

Si la carpeta sugerida no existe para esa persona, el bot muestra las carpetas disponibles. Si hay más de una coincidencia por nombre, no guarda y pide elegir una opción.

Más adelante se conectará Google Drive real para crear carpetas y subir archivos.
