# Depurador de Direcciones

## Objetivo

Sistema offline para limpiar, analizar, consolidar y puntuar direcciones provenientes de archivos Excel o CSV, enfocado inicialmente en direcciones de Chile.

El sistema no depende de APIs externas para su logica principal. La IA mediante Ollama se usa solo como apoyo textual controlado.

## Flujo General

1. Carga un archivo Excel o CSV.
2. Identifica la columna de direccion.
3. Limpia y normaliza el texto.
4. Extrae componentes basicos de direccion.
5. Valida comuna y region usando el maestro territorial BCN.
6. Calcula score de calidad.
7. Agrupa direcciones por `RUT+DV`.
8. Consolida direcciones similares.
9. Mantiene multiples direcciones si son realmente distintas.
10. Detecta duplicados exactos y similares.
11. Ejecuta auditoria de calidad.
12. Exporta un Excel final con hojas de resumen y trazabilidad.

## Componentes Principales

- `src/main.py`: orquestacion del pipeline CLI.
- `src/dataio/loader.py`: carga CSV/Excel y seleccion de columna de direccion.
- `src/dataio/exporter.py`: exportacion a Excel con hojas finales y tecnicas.
- `src/normalization/cleaner.py`: limpieza textual, normalizacion y reglas deterministicas.
- `src/parsing/address_parser.py`: separacion de direccion base, numero y detalles.
- `src/catalog/chile_geo.py`: validacion territorial de comuna, ciudad y region.
- `src/scoring/scorer.py`: scoring interno de calidad.
- `src/dedup/deduplicator.py`: duplicados exactos y similares.
- `src/consolidation/consolidator.py`: consolidacion por `RUT+DV`.
- `src/ai/ollama_client.py`: cliente Ollama con fallback de endpoints.
- `src/ai/adjudicator.py`: uso selectivo de IA con validaciones posteriores.
- `src/quality/audit.py`: auditoria de calidad y metricas.

## Maestro Territorial

Fuente base:

- BCN/SIIT para comunas y regiones de Chile.

Archivos relevantes:

- `Maestro/output/maestro_territorial_chile.csv`
- `Maestro/output/alias_territorial_chile.csv`

Uso del maestro:

- validar comunas,
- resolver region desde comuna valida,
- manejar alias territoriales,
- no validar calles ni numeracion.

## Reglas De Comuna, Ciudad Y Region

1. Si `COMUNA` viene valida, se respeta.
2. Si `COMUNA` no viene y `CIUDAD` coincide con una comuna valida, se usa como comuna.
3. Si `COMUNA` y `CIUDAD` vienen vacias o con `0`, se dejan vacias.
4. `region` se deriva solo desde una comuna valida del maestro BCN.
5. No se infiere comuna desde el texto de `direccion`.
6. La IA no completa ni corrige comuna, ciudad ni region.

## Reglas De Numero

1. Si la columna `NUMERO` viene valida y es mayor que `0`, se usa.
2. Si `NUMERO` viene vacio o `0`, el campo `numero` queda vacio.
3. No se extrae numero desde la direccion.
4. Si el numero valido de columna esta repetido dentro de `direccion`, puede eliminarse del texto final para evitar duplicidad.

## Reglas De Direccion

La direccion se limpia y normaliza mediante reglas deterministicas.

Reglas generales:

- quitar ruido evidente sin borrar informacion util,
- separar texto y numero cuando vienen pegados,
- normalizar abreviaturas frecuentes,
- conservar terminos que forman parte real de la direccion,
- evitar recortes agresivos,
- mantener una salida legible para usuario final.

Ejemplos de terminos relevantes que no deben perderse facilmente:

- `villa`
- `poblacion`
- `sector`
- `condominio`
- `pasaje`
- `calle`
- `avenida`

## Reglas Deterministicas Especiales

Se agregaron correcciones puntuales para casos reales de palabras pegadas o repetidas detectadas en datos de prueba.

Ejemplos ya cubiertos:

- `costaneratalagante` -> `costanera talagante`
- `centralquilicura` -> `central quilicura`
- `quellonquellon` -> `quellon`
- `salinastalcahuano` -> `salinas talcahuano`
- `puntillapirque` -> `puntilla pirque`
- `cantohualpen` -> `canto hualpen`
- `franckepuyehue` -> `francke puyehue`
- `catalunacurico` -> `cataluna curico`
- `tierraamarilla` -> `tierra amarilla`

Estas reglas existen para corregir patrones ya observados sin depender de IA cuando el arreglo puede hacerse de forma segura.

## Reglas De Consolidacion

La consolidacion se realiza por `RUT+DV`.

Reglas principales:

1. No se fuerza una sola direccion por persona.
2. Si hay variantes muy similares, se conserva la mejor representante del cluster.
3. Si hay direcciones realmente distintas para el mismo `RUT+DV`, se conservan multiples filas.
4. Se priorizan registros con mejor calidad y mayor completitud.

La consolidacion busca evitar duplicados sin destruir informacion potencialmente valida.

## Uso De IA Con Ollama

La IA se usa como apoyo textual y no como fuente de verdad estructural.

Configuracion operativa actual:

- modelo por defecto: `gemma4:e2b`
- endpoint principal: `/api/chat`
- fallback si responde `404`: `/api/generate`

La IA puede:

- separar palabras pegadas,
- reducir repeticiones innecesarias,
- mejorar legibilidad del texto,
- proponer una mejor version de `direccion`.

La IA no puede:

- completar `numero`,
- completar `comuna`,
- completar `ciudad`,
- completar `region`,
- inventar datos,
- sobreescribir datos estructurados validos.

## Guardrails De IA

Una propuesta de IA solo se aplica si mejora la calidad de forma objetiva.

Validaciones relevantes:

- confianza alta,
- mejora textual real,
- no introduce nuevos errores,
- no elimina informacion importante,
- no produce una direccion peor que la base.

Si no cumple estas reglas, se rechaza el cambio y se conserva la version deterministica.

## Auditoria De Calidad

El sistema genera alertas para revisar problemas residuales sin inspeccionar manualmente todas las filas.

Tipos de alerta usados en esta etapa:

- `DIRECCION_VACIA_CON_DATOS`
- `PALABRA_PEGADA_REVISAR`
- `REPETICION_PEGADA`
- `DIRECCION_CORTA_VALIDA`
- `DIRECCION_CORTA_REVISAR`
- `RESIDUO_TERRITORIAL_DIRECCIONAL`
- `TOKEN_CERO_AISLADO`
- `COMUNA_FALTANTE`

Las metricas permiten medir avance de calidad entre corridas.

## Excel De Salida

Hojas generadas:

- `resumen`: salida principal visible.
- `detalle_tecnico`: trazabilidad tecnica oculta con estado `hidden`.
- `duplicados_exactos`: registros detectados como exactos.
- `duplicados_similares`: registros similares segun umbral.
- `calidad_direcciones`: alertas de calidad por fila.
- `metricas_calidad`: resumen agregado de indicadores.

Columnas finales esperadas en `resumen`:

- `RUT`
- `DV`
- `RUT+DV`
- `NOMBRE`
- `direccion`
- `numero`
- `comuna`
- `ciudad`
- `region`

## Estado De Esta Version

Esta version puede considerarse estable como base operativa del proyecto.

Se considera estable porque:

- el pipeline principal esta implementado de extremo a extremo,
- las reglas criticas ya quedaron acotadas,
- la IA esta contenida por guardrails,
- existe auditoria para seguir mejorando sin romper la base.

No se considera cerrada de forma definitiva. La idea es usar esta version como base estable mientras se agregan nuevas reglas o nuevas bases de apoyo.

## Pendientes Naturales

- seguir corrigiendo casos residuales de palabras pegadas,
- incorporar nuevas bases auxiliares si aportan valor real,
- calibrar nuevas reglas sin afectar estabilidad,
- evaluar mejoras futuras de interfaz para carga y descarga de archivos.
