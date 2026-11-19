# Áurea · Proyecto 3: implementación OLAP

Pipeline: **CSV → staging → limpieza → modelo estrella PostgreSQL → vistas → Power BI Desktop**.

## Archivos de entrega

- `data/`: los dos CSV originales, copiados sin cambios.
- `originales/`: los nueve scripts recibidos, conservados como referencia.
- `sql/`, `cargar.py` y `cargar.psql`: procesamiento, limpieza, ingesta y validación.
- `powerbi/Aurea.pbip`: proyecto editable de Power BI; conservar sus dos carpetas acompañantes.
- `output/modelo_y_analisis.pdf`: documentación del modelo, campos, relaciones y decisiones.
- `output/aurea_olap.sql`: dump SQL de PostgreSQL, sin propietarios ni privilegios.
- `output/pruebas_postgresql.json`: evidencia de carga, idempotencia, restricciones y restauración.
- `docs/guion_presentacion.md`: exposición de 18 minutos con demostración del tablero.
- `output/referencia_tablero.pdf`: referencia visual calculada desde los CSV; **no es una exportación de Power BI**.

La exportación definitiva del tablero debe realizarse desde Power BI Desktop después de actualizar los datos. El PBIP contiene la definición, pero no un caché de datos ni credenciales.

### Estado de la revisión local

El proyecto abrió correctamente en Power BI Desktop 2.159.1231.0. La actualización está pendiente del acceso manual a PostgreSQL. Durante esta revisión, el parámetro Servidor apunta a `127.0.0.1:55432`, una instancia de prueba aislada en `tmp/olap-test/data`, con base `PRF_Aurea_OLAP` y usuario `aurea_olap`. La contraseña local está en `tmp/olap-test/password.txt` y se excluye del paquete. Esta instancia no es un servicio permanente: para presentar en otra computadora, restaurar el dump y configurar el servidor propio siguiendo los pasos siguientes.

Los archivos PBIR pasaron validación estructural contra los esquemas oficiales. Aún debe completarse la revisión visual con datos y la exportación nativa a PDF; la referencia visual incluida no sustituye esa entrega.

## 1. Crear una base analítica independiente

Usar una base **vacía** llamada `PRF_Aurea_OLAP`. No ejecutar los scripts del Proyecto 2: los CSV ya son las fuentes crudas de este proyecto.

En pgAdmin: Databases → Create → Database → `PRF_Aurea_OLAP`.

Con las herramientas PostgreSQL en el PATH:

```powershell
createdb -h localhost -p 5432 -U postgres PRF_Aurea_OLAP
```

La contraseña se introduce cuando PostgreSQL la solicita; no se guarda en el repositorio. Estos comandos asumen el puerto local estándar; usar el puerto real de la instalación si difiere.

## 2. Validar y cargar los CSV

Desde una terminal situada en la carpeta `olap`:

```powershell
python cargar.py --solo-validar
psql -X -h localhost -p 5432 -U postgres -d PRF_Aurea_OLAP -f cargar.psql
```

El primer comando solo requiere Python estándar. El segundo usa `psql`; **cargar.psql no se ejecuta en Query Tool**, porque contiene órdenes `\copy` y `\ir` propias de psql. Si psql no está en el PATH, usar `& 'C:/Program Files/PostgreSQL/18/bin/psql.exe'` seguido de los argumentos.

Alternativa en un solo paso: definir `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD` y `PGDATABASE`, y ejecutar `python cargar.py`. Este comando valida los CSV y llama a psql; no necesita paquetes Python externos. Se puede indicar `--pg-bin` si psql no está en el PATH. Nunca pegar una contraseña en archivos que se subirán a GitHub.

La carga valida los archivos, sustituye staging dentro de una transacción y agrega los hechos que no existen. Las fuentes idénticas se pueden cargar de nuevo. Si cambió una venta ya cargada, la reconciliación falla y revierte la transacción; este pipeline de entrega no implementa CDC ni actualización histórica. Para fuentes modificadas, crear otra base OLAP vacía.

### Resultados esperados

| Fuente | Líneas | Compras | Unidades | Ventas Q | Ticket Q |
|---|---:|---:|---:|---:|---:|
| Proyecto 2 | 1,563 | 478 | 2,363 | 114,258.00 | 239.03 |
| Simulado SQL | 6,619 | 2,026 | 10,965 | 529,904.00 | 261.55 |

Hay 8,182 hechos, 128 fechas continuas, 3 sucursales, 21 platillos y 31 miembros de cliente, incluido el miembro 0 sin identificar. El nombre “Proyecto 2” identifica la procedencia; no demuestra que sean ventas comerciales reales.

## 3. Abrir Power BI

1. Abrir `powerbi/Aurea.pbip` con Power BI Desktop actualizado. Si la versión requiere habilitar proyectos PBIP, usar Archivo → Opciones → Características de versión preliminar y reiniciar.
2. En Transformar datos → Editar parámetros, indicar `Servidor` (`localhost:5432`) y `BaseDatos` (`PRF_Aurea_OLAP`).
3. Actualizar. En el diálogo de autenticación PostgreSQL, introducir personalmente el usuario y contraseña de la base. La consulta usa `datamart.v_ventas_analisis` en modo Importar.
4. En Vista → Temas → Examinar temas, importar `tema_aurea.json` para aplicar la paleta verde y oro.
5. Revisar los cuatro indicadores de la primera página contra la tabla anterior. Probar filtros de sucursal, categoría y fecha, y limpiar la selección antes de exportar.
6. Guardar como `Aurea.pbix` si se quiere una copia con datos importados para presentar sin conexión. Conservar el PBIP como código fuente editable.
7. Archivo → Exportar → Exportar a PDF. Guardar el resultado como `output/tablero_powerbi.pdf`.

### Páginas y gráficos

| Página | Contenido | Pregunta de negocio |
|---|---|---|
| Resumen ejecutivo | 4 KPIs, líneas, barras, dona y columnas | ¿Cuánto vendemos, dónde y a qué hora? |
| Portafolio y decisiones | Treemap, dispersión y ranking en barras | ¿Qué productos concentran ingresos y unidades? |
| Escenario simulado | Resumen separado del conjunto sintético | ¿Cómo funciona el análisis con un período más amplio? |

Se usan **seis tipos de gráfico distintos**, además de tarjetas y segmentadores. Las páginas 1 y 2 filtran `Proyecto 2`; la página 3 filtra `Simulado SQL`. No cambiar esos filtros para mostrar un crecimiento ficticio entre fuentes.

El SQL conserva el modelo estrella. Power BI importa una vista desnormalizada construida sobre ese modelo, tal como pide la arquitectura del proyecto. No se suman tickets ni conteos distintos preagregados: las medidas DAX se recalculan sobre las líneas filtradas.

## 4. Respaldo y restauración

El dump incluido se generó con PostgreSQL 18 y se restauró y validó con la misma versión.

```powershell
createdb -h localhost -p 5432 -U postgres Aurea_OLAP_Restaurada
psql -X -v ON_ERROR_STOP=1 -h localhost -p 5432 -U postgres -d Aurea_OLAP_Restaurada -f output/aurea_olap.sql
psql -X -v ON_ERROR_STOP=1 -h localhost -p 5432 -U postgres -d Aurea_OLAP_Restaurada -f sql/05_validacion.sql
```

Restaurar únicamente sobre una base vacía. Para generar un respaldo actualizado:

```powershell
pg_dump -h localhost -p 5432 -U postgres -d PRF_Aurea_OLAP --no-owner --no-privileges -f output/aurea_olap.sql
```

## 5. Reproducir las pruebas

`python verificar.py --pg-bin 'C:/Program Files/PostgreSQL/18/bin'` usa las variables PG de una instancia de pruebas. Crea dos bases con nombres únicos, carga dos veces, intenta introducir errores y restaura el dump en la segunda base. No borra bases existentes.

## Alcance del análisis

- Las fuentes no contienen costos, descuentos, impuestos, stock ni tiempos de servicio. No se calcula utilidad, margen ni rotación de inventario.
- El ticket es ventas de las líneas seleccionadas dividido entre compras distintas que contienen esas líneas. Al filtrar una categoría deja de representar el total completo de cada orden.
- Un cliente no identificado se asigna a 0 y se excluye del conteo de clientes identificados.
- Las fechas se convierten desde su offset a `America/Guatemala` antes de extraer día y hora.
- La simulación recibida repite días de la plantilla y ajusta cantidades de forma determinista. No es un pronóstico ni una muestra independiente.
- Hay 22 días en el período del Proyecto 2 y 92 en el simulado. No comparar ventas totales como si los períodos y orígenes fueran equivalentes.

## Referencias de implementación

- [Proyectos Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [Formato del reporte PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Modelo semántico y model.bim](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset)
- [Esquemas JSON oficiales](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report)
