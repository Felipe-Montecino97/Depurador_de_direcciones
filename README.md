# Depurador de Direcciones

Proyecto para limpiar, analizar y puntuar direcciones desde archivos Excel o CSV.

## Objetivo

Crear un depurador de direcciones sin conexión a APIs externas.

El sistema debe:
- Limpiar direcciones sin eliminar información importante.
- Evitar descartar automáticamente direcciones largas.
- Detectar duplicados exactos y similares.
- Analizar palabra por palabra si una dirección tiene sentido.
- Asignar un score interno de calidad.
- Exportar un archivo con los resultados depurados.

## Estructura actual

El flujo está separado por responsabilidad:

- `src/loader.py`: carga CSV/Excel y selecciona columna de direcciones.
- `src/cleaner.py`: limpieza y normalización sin eliminar direcciones largas.
- `src/scorer.py`: scoring palabra por palabra con razones y análisis por token.
- `src/deduplicator.py`: detección de duplicados exactos y similares.
- `src/exporter.py`: exportación a Excel en múltiples hojas.
- `src/main.py`: orquestación del pipeline offline completo.

## Uso

```bash
python src/main.py --input data/input/archivo.xlsx --output data/output/resultado_depurado.xlsx --column direccion --threshold 88
```

Parámetros:
- `--input`: archivo fuente CSV o Excel.
- `--output`: ruta del Excel de salida.
- `--column`: columna de direcciones (opcional).
- `--threshold`: umbral para similares (por defecto 88).
