"""Valida PBIR contra los esquemas públicos de Microsoft y sus referencias internas."""
import json
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urldefrag
import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parent/'tmp/pbir-schemas'
CACHE.mkdir(parents=True,exist_ok=True)


def retrieve(uri):
    uri=urldefrag(uri)[0]
    relative=uri.split('/json-schemas/')[-1] if '/json-schemas/' in uri else uri.split('/main/')[-1]
    path=CACHE/relative
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        url='https://raw.githubusercontent.com/microsoft/json-schemas/main/'+relative
        subprocess.run(['curl.exe','--fail','--silent','--show-error','--connect-timeout','15','--max-time','90','-L','-o',str(path),url],check=True)
    schema=json.loads(path.read_text(encoding='utf-8'))
    # Referencias relativas deben resolverse respecto al URI solicitado, incluso
    # cuando el identificador embebido usa schema.embedded.json con punto.
    schema['$id']=uri
    return Resource.from_contents(schema,default_specification=DRAFT7)


def main():
    registry=Registry(retrieve=retrieve)
    reports=[]
    for path in sorted((ROOT/'powerbi').rglob('*.json')):
        obj=json.loads(path.read_text(encoding='utf-8'))
        if '$schema' not in obj:continue
        schema=retrieve(obj['$schema']).contents
        jsonschema.Draft7Validator(schema,registry=registry).validate(obj)
        reports.append(str(path.relative_to(ROOT)))
    path=ROOT/'powerbi/Aurea.Report/definition.pbir'
    obj=json.loads(path.read_text(encoding='utf-8'))
    jsonschema.Draft7Validator(retrieve(obj['$schema']).contents,registry=registry).validate(obj)
    model=json.loads((ROOT/'powerbi/Aurea.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
    table=model['tables'][0]
    cols={x['name'] for x in table['columns']};measures={x['name'] for x in table['measures']}
    kinds=set()
    for path in (ROOT/'powerbi').rglob('visual.json'):
        v=json.loads(path.read_text(encoding='utf-8'))['visual'];kinds.add(v['visualType'])
        for role in v.get('query',{}).get('queryState',{}).values():
            for p in role['projections']:
                for kind,expr in p['field'].items():
                    assert expr['Property'] in (measures if kind=='Measure' else cols),(path,expr)
    results={'estado':'APROBADO','archivos_con_esquema':len(reports)+1,'tipos_visuales':sorted(kinds),
      'alcance':'Validación estructural JSON y referencias de campos; no sustituye apertura y actualización en Power BI Desktop.'}
    (ROOT/'output/validacion_powerbi.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
