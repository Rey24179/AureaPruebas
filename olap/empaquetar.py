"""Empaqueta la entrega local, excluyendo cachés, credenciales y temporales."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent
allowed={'.csv','.sql','.py','.psql','.md','.json','.pbip','.pbir','.pbism','.bim','.pdf','.dax','.txt','.pbix'}
files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and p.suffix.lower() in allowed
       and not any(part in ('.pbi','__pycache__','.local') or part.startswith('.env') for part in p.relative_to(ROOT).parts)
       and p.name!='manifest_entrega.json']
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifest_path=ROOT/'output/manifest_entrega.json'
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=ROOT/'output/entrega_aurea_olap.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for p in files+[manifest_path]:z.write(p,'Aurea_OLAP/'+p.relative_to(ROOT).as_posix())
with ZipFile(archive) as z:
    assert z.testzip() is None
print(f'{archive.name}: {len(files)+1} archivos, {archive.stat().st_size:,} bytes')
