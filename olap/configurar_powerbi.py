"""Configura servidor y base del PBIP sin guardar credenciales."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--servidor',required=True,help='Ejemplo: localhost:5432')
parser.add_argument('--base',default='PRF_Aurea_OLAP')
args=parser.parse_args()
path=Path(__file__).resolve().parent/'powerbi/Aurea.SemanticModel/model.bim'
data=json.loads(path.read_text(encoding='utf-8'))
for item in data['model']['expressions']:
    value={'Servidor':args.servidor,'BaseDatos':args.base}.get(item['name'])
    if value is not None:
        item['expression']='"'+value.replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Conexión configurada. Cerrar y volver a abrir el PBIP si estaba abierto.')
