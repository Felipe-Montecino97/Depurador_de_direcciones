# Maestro Territorial

Estructura recomendada para catalogos territoriales:

- `Maestro/raw/`: archivos fuente originales (ZIP BCN).
- `Maestro/work/`: extraccion temporal de shapefiles.
- `Maestro/output/`: CSV listos para el pipeline.
- `Maestro/docs/`: trazabilidad de fuentes y fecha de extraccion.

Script de construccion:

```bash
python scripts/build_chile_catalog.py --base-dir Maestro
```
