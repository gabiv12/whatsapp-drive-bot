# Google Drive Setup

Este documento prepara la etapa de Google Drive real. Todavía no hay integración activa en el código.

## Concepto

La cuenta de Drive del cliente será la que almacenará los documentos.

No se debe hardcodear el correo del cliente en el código. El correo del cliente se usará para autenticación o configuración, y los datos sensibles deberán ir por variables de entorno o credenciales seguras del entorno de deploy.

## Carpeta Raíz

Crear en Google Drive una carpeta raíz:

```text
Documentos Kani
```

Guardar el ID de esa carpeta en la variable de entorno:

```text
GOOGLE_DRIVE_ROOT_FOLDER_ID=
```

## Carpetas Por Persona

Dentro de `Documentos Kani`, cada persona tendrá su carpeta raíz:

```text
Documentos Kani/
├── Fernando Gutman/
└── Pablo Sanchez/
```

Más adelante, cada carpeta interna `C 001`, `C 002`, `C 003`, etc. tendrá una carpeta real en Drive.

El campo `drive_folder_id` de `data/folders.json` será el vínculo entre el catálogo local y la carpeta real de Google Drive.

Ejemplo:

```json
{
  "code": "C 001",
  "option": "1",
  "name": "C 001",
  "description": "Carpeta 1 de Fernando Gutman",
  "drive_folder_id": "ID_REAL_DE_GOOGLE_DRIVE"
}
```

## Sincronización Con La PC

La PC del cliente sincronizará documentos usando Google Drive para escritorio.

El sistema no se conectará directamente a la PC. El flujo futuro será:

```text
WhatsApp -> Bot -> Google Drive -> Google Drive para escritorio -> PC del cliente
```

Cuando se implemente la subida real, el bot cargará archivos en la carpeta correspondiente de Drive y Google Drive para escritorio se encargará de sincronizarlos con la PC.
