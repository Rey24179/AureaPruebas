-- Debe terminar sin excepciones. Compara cada fila, no solo totales.
DO $$
DECLARE diferencias bigint;
BEGIN
 WITH fuente AS (
   SELECT origen_datos,orden_id,fecha,sucursal_id,platillo_id,COALESCE(cliente_id,0) AS cliente_id,
          hora,cantidad,precio_unitario,importe FROM staging.v_ventas_todas
 ), destino AS (
   SELECT origen_datos,orden_id,fecha,sucursal_id,platillo_id,cliente_id,
          hora,cantidad,precio_unitario,importe FROM datamart.fact_ventas
 )
 SELECT (SELECT COUNT(*) FROM (SELECT * FROM fuente EXCEPT ALL SELECT * FROM destino) a)
      + (SELECT COUNT(*) FROM (SELECT * FROM destino EXCEPT ALL SELECT * FROM fuente) b)
 INTO diferencias;
 IF diferencias <> 0 THEN RAISE EXCEPTION 'Carga inconsistente: % filas diferentes', diferencias; END IF;
 IF (SELECT COUNT(*) FROM datamart.fact_ventas) <> (SELECT COUNT(*) FROM datamart.v_ventas_analisis)
 THEN RAISE EXCEPTION 'La vista pierde o multiplica hechos'; END IF;
 IF EXISTS (
   SELECT 1 FROM staging.v_ventas_todas s JOIN datamart.dim_sucursal d USING(sucursal_id)
   WHERE s.nombre_sucursal <> d.nombre_sucursal
 ) OR EXISTS (
   SELECT 1 FROM staging.v_ventas_todas s JOIN datamart.dim_platillo d USING(platillo_id)
   WHERE (s.nombre_platillo,s.categoria) IS DISTINCT FROM (d.nombre_platillo,d.categoria)
 ) THEN RAISE EXCEPTION 'Catálogos inconsistentes'; END IF;
END $$;

SELECT * FROM datamart.v_kpis_origen ORDER BY origen_datos;
