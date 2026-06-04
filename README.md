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

- `src/dataio/loader.py`: carga CSV/Excel y selecciona columna de direcciones.
- `src/normalization/cleaner.py`: limpieza y normalización sin eliminar información importante.
- `src/scoring/scorer.py`: scoring palabra por palabra con razones y análisis por token.
- `src/dedup/deduplicator.py`: detección de duplicados exactos y similares.
- `src/dataio/exporter.py`: exportación a Excel en múltiples hojas.
- `src/catalog/chile_geo.py`: validación territorial de comuna y región.
- `src/parsing/address_parser.py`: parsing conservador de dirección y número.
- `src/consolidation/consolidator.py`: consolidación por `RUT+DV`.
- `src/quality/audit.py`: auditoría de calidad y métricas.
- `src/ai/adjudicator.py`: mejora textual opcional con IA bajo guardrails.
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

## Documentación

- `docs/funcionamiento_y_reglas.md`: explicación funcional completa del programa y reglas de negocio vigentes.
- `docs/version_estable.md`: definición de la base estable actual y decisiones congeladas para esta etapa.
