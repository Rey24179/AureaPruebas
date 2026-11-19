# Presentación · Áurea OLAP

Duración objetivo: 18 minutos, dejando 2 minutos de margen. Preparar Power BI abierto, datos actualizados, filtros limpios y PDF exportado como respaldo.

## 0:00–2:00 · Caso de negocio

“Áurea necesita decidir qué productos priorizar, cómo distribuir la atención entre sucursales y en qué horarios reforzar el servicio. El tablero usa ventas del Proyecto 2 y un escenario simulado separado. Nuestro análisis identifica oportunidades que deben validarse con un piloto.”

Mostrar el resumen: Q114,258; 478 compras; 2,363 unidades; ticket Q239.03. Aclarar que se trata del dataset académico del Proyecto 2, no de una afirmación sobre ventas reales de una empresa.

## 2:00–4:00 · Fuentes y tratamiento

Mostrar los dos CSV: 1,563 y 6,619 líneas. Explicar que las fechas del primer archivo van del 15 de octubre al 5 de noviembre y las del simulado del 1 de julio al 30 de septiembre de 2026. No interpretar esa secuencia como crecimiento observado.

Ejemplo: una orden de tres platillos genera tres filas; se suma el importe de las tres, pero la compra se cuenta una vez. Las fechas se convierten a Guatemala y los clientes vacíos se conservan como sin identificar.

## 4:00–6:00 · Modelo y confiabilidad

Mostrar el diagrama estrella del PDF: fact_ventas al centro, dimensiones fecha, sucursal, platillo y cliente. Definir el grano: origen + orden + platillo. Mostrar la vista v_ventas_analisis como entrada de Power BI.

“Repetimos la carga y no duplicó datos. Intentamos cantidades negativas, referencias inexistentes y un importe incorrecto: PostgreSQL los rechazó. Restauramos el dump en otra base y reconciliamos cada fila.” Mostrar pruebas_postgresql.json.

## 6:00–10:00 · Demostración del resumen

1. Mostrar los KPIs sin filtros y explicar el ticket como cociente de ventas y compras distintas.
2. Seleccionar Roosevelt: Q42,000 y 175 compras. Limpiar la selección.
3. Mostrar las categorías: Plato Fuerte aporta Q61,410, equivalentes a 53.75 % del importe del período.
4. Mostrar compras por hora: 109 a las 12 y 175 a las 13; juntas representan 59.41 % de 478 compras.
5. Probar el filtro de fecha y explicar que las tarjetas se recalculan. Limpiar los filtros.

## 10:00–13:00 · Productos y decisiones

Mostrar el treemap y el ranking: Pollo en salsa de champiñones aporta Q12,810 con 122 unidades. En la dispersión, explicar que precio medio = importe/unidades y que el tamaño indica ventas; un precio mayor no demuestra margen mayor.

Propuesta 1: revisar preparación y cobertura de personal alrededor de las 12–14 h. Piloto de dos semanas; medir espera y compras por hora, recolectando primero los tiempos de servicio que faltan.

Propuesta 2: proteger disponibilidad de los productos líderes. Registrar quiebres de stock y desperdicio antes de aumentar compras; no se conoce el inventario en este dataset.

Propuesta 3: probar una oferta de plato y bebida en una sucursal. Comparar ticket, unidades por compra y margen cuando se incorporen costos; no prometer un aumento de ventas.

## 13:00–15:00 · Escenario simulado

Abrir la tercera página y señalar el rótulo de datos simulados. Explicar que el SQL recibido reutiliza patrones diarios y modifica cantidades de forma determinista. Se usa para demostrar amplitud temporal y funcionamiento del pipeline. No usarlo para justificar decisiones operativas reales.

## 15:00–17:00 · Limitaciones y siguientes pasos

El dataset no trae costos, descuentos, impuestos, inventario ni tiempos de atención. La ventana del Proyecto 2 es corta. Esos límites impiden concluir rentabilidad, causalidad o estacionalidad anual.

Siguiente iteración: integrar costos y servicio, ampliar historia, registrar promociones y evaluar el piloto con períodos comparables. Mostrar que el pipeline puede ejecutarse de nuevo y que detecta cambios incompatibles.

## 17:00–18:00 · Cierre y preguntas

“Entregamos fuentes, transformación SQL/Python, modelo estrella, vistas, proyecto Power BI, documentación y dump verificable. Las prioridades propuestas son cobertura al mediodía, disponibilidad de líderes y una prueba medible de venta cruzada.”

Preguntas previsibles:

- **¿Por qué no sumar compras por producto?** Una orden puede aparecer en varios productos; se usa DISTINCTCOUNT de compra_clave.
- **¿Por qué cliente 0?** Representa ventas anónimas sin romper la llave foránea ni inventar personas.
- **¿Por qué una vista plana en Power BI?** La estrella está en PostgreSQL; la vista une hechos y dimensiones para el producto analítico.
- **¿Por qué no comparar julio con octubre?** Son fuentes y duraciones distintas; julio es simulado.
- **¿El líder es el más rentable?** No se puede concluir sin costos.
