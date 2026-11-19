CREATE OR REPLACE VIEW staging.v_ventas_limpias AS
WITH datos_tipados AS (
    SELECT
        TRIM(orden_id)::integer AS orden_id,

        -- Convertir a la hora local de Guatemala.
        TRIM(fecha_hora)::timestamptz
            AT TIME ZONE 'America/Guatemala' AS fecha_hora_local,

        TRIM(sucursal_id)::integer AS sucursal_id,
        TRIM(nombre_sucursal) AS nombre_sucursal,

        -- Un cliente vacío permanece sin identificar.
        CASE
    WHEN cliente_id IS NULL
         OR UPPER(TRIM(cliente_id)) IN ('', 'NULL')
    THEN NULL
    ELSE TRIM(cliente_id)::integer
END AS cliente_id,

        TRIM(platillo_id)::integer AS platillo_id,
        TRIM(nombre_platillo) AS nombre_platillo,
        TRIM(categoria) AS categoria,
        TRIM(cantidad)::integer AS cantidad,
        TRIM(precio_unitario)::numeric(10,2) AS precio_unitario
    FROM staging.ventas_originales
)
SELECT
    orden_id,
    fecha_hora_local,
    fecha_hora_local::date AS fecha,
    EXTRACT(HOUR FROM fecha_hora_local)::integer AS hora,
    sucursal_id,
    nombre_sucursal,
    cliente_id,
    platillo_id,
    nombre_platillo,
    categoria,
    cantidad,
    precio_unitario,
    (cantidad * precio_unitario)::numeric(12,2) AS importe,
    'Proyecto 2'::text AS origen_datos
FROM datos_tipados;

CREATE OR REPLACE VIEW staging.v_ventas_simuladas_limpias AS
WITH datos_tipados AS (
    SELECT
        TRIM(orden_id)::integer AS orden_id,

        TRIM(fecha_hora)::timestamptz
            AT TIME ZONE 'America/Guatemala' AS fecha_hora_local,

        TRIM(sucursal_id)::integer AS sucursal_id,
        TRIM(nombre_sucursal) AS nombre_sucursal,

        CASE
            WHEN cliente_id IS NULL
                 OR UPPER(TRIM(cliente_id)) IN ('', 'NULL')
            THEN NULL
            ELSE TRIM(cliente_id)::integer
        END AS cliente_id,

        TRIM(platillo_id)::integer AS platillo_id,
        TRIM(nombre_platillo) AS nombre_platillo,
        TRIM(categoria) AS categoria,
        TRIM(cantidad)::integer AS cantidad,
        TRIM(precio_unitario)::numeric(10,2) AS precio_unitario

    FROM staging.ventas_simuladas
)
SELECT
    orden_id,
    fecha_hora_local,
    fecha_hora_local::date AS fecha,
    EXTRACT(HOUR FROM fecha_hora_local)::integer AS hora,
    sucursal_id,
    nombre_sucursal,
    cliente_id,
    platillo_id,
    nombre_platillo,
    categoria,
    cantidad,
    precio_unitario,
    (cantidad * precio_unitario)::numeric(12,2) AS importe,
    'Simulado SQL'::text AS origen_datos
FROM datos_tipados;

CREATE OR REPLACE VIEW staging.v_ventas_todas AS SELECT * FROM staging.v_ventas_limpias UNION ALL SELECT * FROM staging.v_ventas_simuladas_limpias;
CREATE OR REPLACE VIEW datamart.v_ventas_analisis AS
SELECT
    v.venta_id,
    v.origen_datos,

    -- Identificador de compra único entre distintos orígenes.
    v.origen_datos || ':' || v.orden_id::text AS compra_clave,

    v.orden_id,
    v.fecha,
    f.anio,
    f.mes,
    f.nombre_mes,
    f.trimestre,
    f.dia_semana,
    f.nombre_dia,
    v.hora,

    v.sucursal_id,
    s.nombre_sucursal,

    v.platillo_id,
    p.nombre_platillo,
    p.categoria,

    v.cliente_id,
    c.etiqueta AS cliente,
    c.identificado AS cliente_identificado,

    v.cantidad,
    v.precio_unitario,
    v.importe

FROM datamart.fact_ventas AS v

JOIN datamart.dim_fecha AS f
    ON f.fecha = v.fecha

JOIN datamart.dim_sucursal AS s
    ON s.sucursal_id = v.sucursal_id

JOIN datamart.dim_platillo AS p
    ON p.platillo_id = v.platillo_id

JOIN datamart.dim_cliente AS c
    ON c.cliente_id = v.cliente_id;
