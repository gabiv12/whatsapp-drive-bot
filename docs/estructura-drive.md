# Estructura Drive

Google Drive será el almacenamiento central del sistema.

El bot no se conectará directamente a la PC del cliente. El flujo futuro será:

```text
WhatsApp -> Bot -> Google Drive -> Google Drive para escritorio en PC del cliente
```

La PC del cliente tendrá instalado Google Drive para escritorio. Esa aplicación se encargará de sincronizar los archivos que el bot suba a Drive, para que el cliente pueda verlos desde el Explorador de Windows.

## Estructura Esperada

```text
Mi unidad/
└── Documentos Kani/
    ├── Fernando Gutman/
    │   ├── C 001/
    │   ├── C 002/
    │   └── C 011 - Facturas carbon enero/
    │
    └── Pablo Sanchez/
        ├── C 001/
        ├── C 002/
        └── C 010/
```

`Documentos Kani` será la carpeta raíz del proyecto en Drive.

Cada persona tendrá su propia carpeta raíz dentro de `Documentos Kani`, por ejemplo `Fernando Gutman` y `Pablo Sanchez`.

Cada carpeta interna del catálogo local, como `C 001`, `C 002` o `C 011`, tendrá una carpeta real equivalente en Drive.

## Relación Con El Catálogo Local

Por ahora, el sistema solo modifica `data/folders.json`. En una etapa posterior, cada carpeta de ese archivo deberá guardar el `drive_folder_id` real asignado por Google Drive.

`drive_folder_id` será el vínculo estable entre el catálogo local y la carpeta real en Drive.

Ejemplo conceptual:

```json
{
  "code": "C 011",
  "option": "11",
  "name": "Facturas carbon enero",
  "description": "Facturas cargadas en enero",
  "drive_folder_id": "google-drive-folder-id"
}
```

`code` identifica la carpeta dentro del sistema. `name` es el nombre visible editable. `drive_folder_id` identificará la carpeta real en Google Drive.

## Renombrado

Renombrar una carpeta no debe crear una carpeta nueva.

Renombrar debe actualizar el nombre visible local y, cuando exista integración real, también el nombre de la carpeta en Drive usando el mismo `drive_folder_id`.

El renombrado debe mantener estables:

- `code`
- `option`
- `drive_folder_id`

El renombrado puede cambiar:

- `name`
- `description`

Esto evita duplicar carpetas y mantiene la relación entre el bot, Google Drive y la PC sincronizada del cliente.
