"""Las fuentes inválidas se rechazan antes de contactar PostgreSQL."""
import csv
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('carga_olap',ROOT/'cargar.py')
carga=importlib.util.module_from_spec(spec)
spec.loader.exec_module(carga)


class FuenteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'data',self.root/'data')
        carga.ROOT=self.root

    def tearDown(self):
        carga.ROOT=ROOT
        self.temp.cleanup()

    def modify(self,change):
        p=self.root/'data/ventas_aurea_p2.csv'
        with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        change(rows)
        with p.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=carga.HEADERS);writer.writeheader();writer.writerows(rows)

    def test_archivos_recibidos(self):
        _,summary=carga.leer_fuentes()
        self.assertEqual([(r['lineas'],r['compras'],r['ventas']) for r in summary],
                         [(1563,478,'114258.00'),(6619,2026,'529904.00')])

    def test_duplicado_no_se_descarta_silenciosamente(self):
        self.modify(lambda rows:rows.append(rows[0].copy()))
        with self.assertRaisesRegex(ValueError,'duplicada'):carga.leer_fuentes()

    def test_cantidad_cero(self):
        self.modify(lambda rows:rows[0].update(cantidad='0'))
        with self.assertRaisesRegex(ValueError,'positivos'):carga.leer_fuentes()

    def test_fecha_sin_offset(self):
        self.modify(lambda rows:rows[0].update(fecha_hora='2026-10-15 08:00:00'))
        with self.assertRaisesRegex(ValueError,'zona horaria'):carga.leer_fuentes()

    def test_nombre_conflictivo_para_misma_clave(self):
        self.modify(lambda rows:rows[0].update(nombre_sucursal='Otra sucursal'))
        with self.assertRaisesRegex(ValueError,'inconsistente'):carga.leer_fuentes()


if __name__=='__main__':unittest.main()
