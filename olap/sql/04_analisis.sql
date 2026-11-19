-- Compras y ticket no son aditivos entre categorías/platillos.
CREATE OR REPLACE VIEW datamart.v_kpis_origen AS
SELECT origen_datos, COUNT(*) AS lineas,
 COUNT(DISTINCT compra_clave) AS compras, SUM(cantidad) AS unidades,
 SUM(importe) AS ventas,
 ROUND(SUM(importe)/NULLIF(COUNT(DISTINCT compra_clave),0),2) AS ticket_promedio,
 MIN(fecha) AS primera_fecha, MAX(fecha) AS ultima_fecha
FROM datamart.v_ventas_analisis GROUP BY origen_datos;

CREATE OR REPLACE VIEW datamart.v_ventas_diarias AS
SELECT origen_datos,fecha,nombre_sucursal,
 SUM(importe) AS ventas, SUM(cantidad) AS unidades,
 COUNT(DISTINCT compra_clave) AS compras
FROM datamart.v_ventas_analisis GROUP BY origen_datos,fecha,nombre_sucursal;

CREATE OR REPLACE VIEW datamart.v_ranking_platillos AS
SELECT origen_datos,platillo_id,nombre_platillo,categoria,
 SUM(importe) AS ventas,SUM(cantidad) AS unidades,
 DENSE_RANK() OVER (PARTITION BY origen_datos ORDER BY SUM(importe) DESC) AS posicion
FROM datamart.v_ventas_analisis
GROUP BY origen_datos,platillo_id,nombre_platillo,categoria;

CREATE OR REPLACE VIEW datamart.v_demanda_horaria AS
SELECT origen_datos,dia_semana,nombre_dia,hora,
 SUM(importe) AS ventas,SUM(cantidad) AS unidades,
 COUNT(DISTINCT compra_clave) AS compras,
 COUNT(DISTINCT fecha) AS dias_observados,
 ROUND(COUNT(DISTINCT compra_clave)::numeric/NULLIF(COUNT(DISTINCT fecha),0),2) AS compras_por_dia_observado
FROM datamart.v_ventas_analisis
GROUP BY origen_datos,dia_semana,nombre_dia,hora;

CREATE INDEX IF NOT EXISTS fact_ventas_fecha_idx ON datamart.fact_ventas(fecha);
CREATE INDEX IF NOT EXISTS fact_ventas_sucursal_idx ON datamart.fact_ventas(sucursal_id);
CREATE INDEX IF NOT EXISTS fact_ventas_platillo_idx ON datamart.fact_ventas(platillo_id);

COMMENT ON TABLE datamart.fact_ventas IS
'Grano: una línea por origen, orden y platillo. Importe bruto; no hay costos, impuestos ni descuentos.';
COMMENT ON VIEW datamart.v_ventas_analisis IS
'Fuente de Power BI. Separar Proyecto 2 y Simulado SQL. compra_clave evita colisiones entre orígenes.';
