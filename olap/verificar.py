"""Prueba carga, reejecución y restauración en una base OLAP de pruebas.

Usa PGHOST, PGPORT, PGUSER y PGPASSWORD. Crea dos bases nuevas con nombres
únicos; no borra bases existentes. Requiere psql, createdb y pg_dump.
"""
import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pg-bin',default='C:/Program Files/PostgreSQL/18/bin')
    args=p.parse_args()
    bindir=Path(args.pg_bin)
    env=os.environ.copy()
    env['PGCLIENTENCODING']='UTF8'
    checks=[]

    def run(exe,*args,fail=False):
        result=subprocess.run([str(bindir/(exe+'.exe' if os.name=='nt' else exe)),*args],env=env,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if (result.returncode==0)==fail:
            raise RuntimeError(result.stderr or result.stdout or 'Se esperaba un fallo')
        return result.stdout

    def query(sql,fail=False):
        # psql Windows convierte los argumentos -c a la página ANSI del sistema.
        # stdin con encoding UTF-8 preserva comentarios y mensajes en español.
        result=subprocess.run([str(bindir/('psql.exe' if os.name=='nt' else 'psql')),
            '-X','-w','-v','ON_ERROR_STOP=1','-At'],input=sql,env=env,cwd=ROOT,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        if (result.returncode==0)==fail:raise RuntimeError(result.stderr or result.stdout or 'Se esperaba un fallo')
        return result.stdout.strip()

    stamp=datetime.now().strftime('%Y%m%d%H%M%S')
    source='aurea_test_'+stamp
    target='aurea_restore_'+stamp
    for db in [source,target]:run('createdb','-w',db)
    env['PGDATABASE']=source
    run('psql','-X','-w','-f','cargar.psql')
    checks.append('Carga completa: 8182 hechos; reconciliación fila por fila')
    baseline=query('SELECT COUNT(*)||\'|\'||SUM(importe) FROM datamart.fact_ventas')
    assert baseline=='8182|644162.00',baseline
    run('psql','-X','-w','-f','cargar.psql')
    assert baseline==query('SELECT COUNT(*)||\'|\'||SUM(importe) FROM datamart.fact_ventas')
    checks.append('Segunda carga idéntica: sin duplicar filas ni importes')
    generator=(ROOT/'originales/06_generar_simulados.sql').read_text(encoding='utf-8-sig').strip().rstrip(';')
    generated_diff=query('WITH generado AS ('+generator+'''), archivo AS (
       SELECT orden_id,fecha_hora_local AT TIME ZONE 'America/Guatemala' AS fecha_hora,
       sucursal_id,nombre_sucursal,cliente_id,platillo_id,nombre_platillo,categoria,cantidad,precio_unitario
       FROM staging.v_ventas_simuladas_limpias)
       SELECT (SELECT COUNT(*) FROM (SELECT * FROM generado EXCEPT ALL SELECT * FROM archivo) a)
            + (SELECT COUNT(*) FROM (SELECT * FROM archivo EXCEPT ALL SELECT * FROM generado) b)''')
    assert generated_diff=='0',generated_diff
    checks.append('Generador SQL recibido reproduce exactamente las 6619 líneas simuladas')
    for label,statement in [
      ('Cantidad negativa', 'UPDATE datamart.fact_ventas SET cantidad=-1 WHERE venta_id=(SELECT MIN(venta_id) FROM datamart.fact_ventas)'),
      ('Dimensión huérfana', 'UPDATE datamart.fact_ventas SET sucursal_id=999999 WHERE venta_id=(SELECT MIN(venta_id) FROM datamart.fact_ventas)'),
      ('Importe incorrecto', 'UPDATE datamart.fact_ventas SET importe=importe+1 WHERE venta_id=(SELECT MIN(venta_id) FROM datamart.fact_ventas)'),
      ('Cambio de fuente detectado', "UPDATE staging.ventas_originales SET cantidad=(cantidad::integer+1)::text WHERE orden_id='2';")]:
        if label=='Cambio de fuente detectado':
            sql='BEGIN;'+statement+(ROOT/'sql/05_validacion.sql').read_text(encoding='utf-8')+'COMMIT;'
        else:sql='BEGIN;'+statement+';COMMIT;'
        query(sql,fail=True)
        assert baseline==query('SELECT COUNT(*)||\'|\'||SUM(importe) FROM datamart.fact_ventas')
        checks.append(label+': rechazo y rollback correctos')
    dump=ROOT/'output/aurea_olap.sql'
    run('pg_dump','-w','--no-owner','--no-privileges','-f',str(dump))
    env['PGDATABASE']=target
    run('psql','-X','-w','-v','ON_ERROR_STOP=1','-f',str(dump))
    assert baseline==query('SELECT COUNT(*)||\'|\'||SUM(importe) FROM datamart.fact_ventas')
    run('psql','-X','-w','-f','sql/05_validacion.sql')
    checks.append('Dump restaurado en una segunda base: reconciliación exacta')
    results={'estado':'APROBADO','motor':query('SELECT version()'),'bases_prueba':[source,target],'comprobaciones':checks}
    (ROOT/'output/pruebas_postgresql.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
