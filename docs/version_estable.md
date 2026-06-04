# Version Estable Base

## Alcance

Esta version se deja como base estable del depurador de direcciones para continuar evolucionando el proyecto sin perder un punto de referencia confiable.

## Que Ya Resuelve

- carga de archivos Excel y CSV,
- limpieza y normalizacion de direcciones,
- parser de direccion y numero con reglas conservadoras,
- validacion territorial con maestro comunal y regional de Chile,
- consolidacion por `RUT+DV` sin colapsar direcciones distintas,
- deteccion de duplicados exactos y similares,
- auditoria de calidad,
- exportacion final con hojas tecnicas y de revision,
- uso opcional de IA con Ollama bajo guardrails.

## Criterio De Estabilidad

Se considera estable porque:

1. Las decisiones criticas de negocio ya fueron fijadas.
2. El comportamiento principal es reproducible.
3. Los casos mas riesgosos ya tienen reglas explicitas.
4. La salida final permite control y trazabilidad.

## Decisiones Relevantes Congeladas En Esta Base

1. No inferir comuna desde el texto de la direccion.
2. No extraer numero desde la direccion cuando `NUMERO` viene vacio o en `0`.
3. Derivar `region` solo desde comuna valida del maestro.
4. Permitir multiples direcciones por `RUT+DV` si realmente son distintas.
5. Usar IA solo para mejorar texto de `direccion`, nunca campos estructurales.
6. Mantener `detalle_tecnico` oculta, no `veryHidden`.

## Como Usarla

Ejemplo sin IA:

```bash
cmd /c py src/main.py --input "EJEMPLOS/EJEMPLO ARCHIVO ORIGEN/ejemplos direcciones depurador.xlsx" --output "data/output/version_estable.xlsx" --column DIRECCION --threshold 88 --disable-ai
```

Ejemplo con IA:

```bash
cmd /c py src/main.py --input "EJEMPLOS/EJEMPLO ARCHIVO ORIGEN/ejemplos direcciones depurador.xlsx" --output "data/output/version_estable_ai.xlsx" --column DIRECCION --threshold 88
```

## Siguiente Etapa

Sobre esta base se pueden agregar:

- nuevas reglas deterministicas,
- nuevas bases de apoyo,
- refinamientos de auditoria,
- mejoras de interfaz,
- recalibracion de IA en casos puntuales.

La recomendacion es tratar esta version como punto de control antes de abrir una nueva ronda de cambios.
