"""Carga transaccional CSV -> staging -> estrella. No modifica el esquema public."""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HEADERS = 'orden_id fecha_hora sucursal_id nombre_sucursal cliente_id platillo_id nombre_platillo categoria cantidad precio_unitario'.split()
SOURCES = [('ventas_aurea_p2.csv', 'Proyecto 2', 'ventas_originales'),
           ('ventas_aurea_simuladas.csv', 'Simulado SQL', 'ventas_simuladas')]


def leer_fuentes():
    datasets, resumen = {}, []
    catalogs = {'sucursal': {}, 'platillo': {}}
    for filename, origen, tabla in SOURCES:
        path = ROOT / 'data' / filename
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != HEADERS:
                raise ValueError(f'{filename}: encabezados diferentes a los esperados')
            rows = list(reader)
        if not rows:
            raise ValueError(f'{filename}: archivo vacío')
        keys, orders, dates, total, units, anonymous = set(), {}, [], Decimal(0), 0, 0
        for line, r in enumerate(rows, 2):
            try:
                r.update({k: v.strip() for k, v in r.items()})
                oid, sid, pid, qty = [int(r[k]) for k in ['orden_id','sucursal_id','platillo_id','cantidad']]
                price = Decimal(r['precio_unitario'])
                dt = datetime.fromisoformat(r['fecha_hora'])
                if dt.tzinfo is None:
                    raise ValueError('fecha sin zona horaria')
                dt = dt.astimezone(timezone(timedelta(hours=-6)))
                cid = None if r['cliente_id'].upper() in ('', 'NULL') else int(r['cliente_id'])
                if min(oid, sid, pid, qty) <= 0 or (cid is not None and cid <= 0):
                    raise ValueError('identificadores/cantidad deben ser positivos; cliente 0 reservado')
                if max(oid, sid, pid, qty, cid or 0) > 2147483647:
                    raise ValueError('valor fuera del rango integer')
                if not price.is_finite() or price < 0 or price != price.quantize(Decimal('.01')) or price >= Decimal('100000000') or qty*price >= Decimal('10000000000'):
                    raise ValueError('precio/importe inválido o fuera de precisión')
                if (oid, pid) in keys:
                    raise ValueError('línea duplicada por orden y platillo')
                keys.add((oid, pid))
                signature = (dt.isoformat(), sid, cid)
                if oid in orders and orders[oid] != signature:
                    raise ValueError('misma orden con fecha, sucursal o cliente diferentes')
                orders[oid] = signature
                for kind, key, value in [('sucursal', sid, r['nombre_sucursal']), ('platillo', pid, (r['nombre_platillo'], r['categoria']))]:
                    if key in catalogs[kind] and catalogs[kind][key] != value:
                        raise ValueError(f'catálogo {kind} inconsistente para {key}')
                    catalogs[kind][key] = value
                if not all(r[k] for k in ['nombre_sucursal', 'nombre_platillo', 'categoria']):
                    raise ValueError('nombre/categoría vacío')
                dates.append(dt.date().isoformat())
                units += qty
                total += qty * price
                anonymous += cid is None
            except (ValueError, ArithmeticError, TypeError, AttributeError) as e:
                raise ValueError(f'{filename}, línea {line}: {e}') from e
        datasets[tabla] = rows
        resumen.append(dict(origen=origen, archivo=filename, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            lineas=len(rows), compras=len(orders), unidades=units, ventas=str(total),
                            ticket_promedio=str((total/len(orders)).quantize(Decimal('.01'))),
                            fecha_inicial=min(dates), fecha_final=max(dates), lineas_sin_cliente=anonymous))
    return datasets, resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-validar', action='store_true')
    parser.add_argument('--pg-bin', help='Carpeta que contiene psql')
    args = parser.parse_args()
    datasets, resumen = leer_fuentes()
    if not args.solo_validar:
        env = os.environ.copy()
        env.setdefault('PGDATABASE', 'PRF_Aurea_OLAP')
        env['PGCLIENTENCODING'] = 'UTF8'
        psql = str(Path(args.pg_bin)/('psql.exe' if os.name == 'nt' else 'psql')) if args.pg_bin else shutil.which('psql')
        if not psql and os.name == 'nt':
            installed = list(Path(os.environ.get('ProgramFiles', 'C:/Program Files')).glob('PostgreSQL/*/bin/psql.exe'))
            if installed: psql = str(sorted(installed, key=lambda p: int(p.parents[1].name) if p.parents[1].name.isdigit() else 0)[-1])
        if not psql:
            raise SystemExit('No se encontró psql. Indicar --pg-bin con la carpeta bin de PostgreSQL.')
        subprocess.run([psql, '-X', '-v', 'ON_ERROR_STOP=1', '-f', str(ROOT/'cargar.psql')],
                       env=env, cwd=ROOT, check=True)
    output = ROOT/'output'
    output.mkdir(exist_ok=True)
    (output/'validacion_fuentes.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print('CSV válidos.' if args.solo_validar else 'Carga confirmada y reconciliada.')


if __name__ == '__main__':
    main()
