"""Genera el proyecto editable PBIP/PBIR y el modelo TMSL de Power BI."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent/'powerbi'
REPORT = ROOT/'Aurea.Report'
MODEL = ROOT/'Aurea.SemanticModel'
BASE = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def literal(value):
    if isinstance(value,bool): value='true' if value else 'false'
    elif isinstance(value,str): value="'"+value.replace("'","''")+"'"
    else: value=str(value)+'D'
    return {'expr':{'Literal':{'Value':value}}}


def color(value):
    return {'solid':{'color':literal(value)}}


def field(name,measure=False):
    return {'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':'Ventas'}},'Property':name}}


def projection(name, measure=False):
    label={'nombre_sucursal':'Sucursal','nombre_platillo':'Platillo','categoria':'Categoría',
           'fecha':'Fecha de venta','hora':'Hora (Guatemala)'}.get(name,name)
    return {'field':field(name,measure),'queryRef':'Ventas.'+name,'nativeQueryRef':name,'displayName':label}


def visual(page,name,kind,title,position,roles=None,sort=None,objects=None):
    x,y,w,h=position
    v={'visualType':kind,'visualContainerObjects':{
        'title':[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(12),'fontColor':color('#203B35')}}],
        'background':[{'properties':{'show':literal(True),'color':color('#FFFFFF'),'transparency':literal(0)}}],
        'border':[{'properties':{'show':literal(False)}}]}}
    if roles:
        v['query']={'queryState':{role:{'projections':[projection(n,m) for n,m in fields]} for role,fields in roles.items()}}
        if sort:
            n,m,d=sort
            v['query']['sortDefinition']={'sort':[{'field':field(n,m),'direction':d}],'isDefaultSort':False}
    if objects: v['objects']=objects
    save(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',{
        '$schema':BASE+'visualContainer/2.1.0/schema.json','name':name,
        'position':{'x':x,'y':y,'width':w,'height':h,'z':y*10+x,'tabOrder':y*10+x},'visual':v})


def text(page,name,content,pos,size=16):
    visual(page,name,'textbox','',pos,objects={'general':[{'properties':{'paragraphs':[
        {'textRuns':[{'value':content,'textStyle':{'fontSize':f'{size}pt','fontFamily':'Segoe UI','color':'#203B35'}}]}]}}]})
    path=REPORT/'definition/pages'/page/'visuals'/name/'visual.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    data['visual']['visualContainerObjects']['title'][0]['properties']['show']=literal(False)
    save(path,data)


def page(name,title,source):
    save(REPORT/'definition/pages'/name/'page.json',{'$schema':BASE+'page/2.0.0/schema.json',
        'name':name,'displayName':title,'displayOption':'FitToPage','width':1280,'height':900,
        'objects':{'background':[{'properties':{'color':color('#F3F0E8'),'transparency':literal(0)}}]},
        'filterConfig':{'filters':[{'name':'Origen_'+name,'field':field('origen_datos'),'type':'Categorical','isLockedInViewMode':True,
           'filter':{'Version':2,'From':[{'Name':'v','Entity':'Ventas','Type':0}],
            'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'v'}},'Property':'origen_datos'}}],
                                      'Values':[[{'Literal':{'Value':"'"+source+"'"}}]]}}}]}}]}})
    text(name,'encabezado','ÁUREA  /  '+title.upper(),(24,16,1232,55),24)
    text(name,'contexto',f'Fuente: {source}  |  Ventas brutas en quetzales  |  Selecciona gráficos para explorar',(24,73,1232,35),11)
    for i,(col,label) in enumerate([('nombre_sucursal','Sucursal'),('categoria','Categoría'),('fecha','Fecha')]):
        opts={'data':[{'properties':{'mode':literal('Dropdown')}}]} if col!='fecha' else None
        visual(name,'filtro_'+col,'slicer',label,(24+i*416,116,400,80),{'Values':[(col,False)]},objects=opts)


def main():
    measures=[
       ('Ventas Q','SUM(Ventas[importe])','"Q" #,0.00'),
       ('Compras','DISTINCTCOUNT(Ventas[compra_clave])','#,0'),
       ('Unidades','SUM(Ventas[cantidad])','#,0'),
       ('Ticket promedio Q','DIVIDE([Ventas Q], [Compras])','"Q" #,0.00'),
       ('Precio medio Q','DIVIDE([Ventas Q], [Unidades])','"Q" #,0.00'),
       ('Clientes identificados','CALCULATE(DISTINCTCOUNT(Ventas[cliente_id]), Ventas[cliente_identificado] = TRUE())','#,0'),
       ('Dias con ventas','DISTINCTCOUNT(Ventas[fecha])','#,0'),
       ('Ventas por dia Q','DIVIDE([Ventas Q], [Dias con ventas])','"Q" #,0.00')]
    strings='origen_datos compra_clave nombre_mes nombre_dia nombre_sucursal nombre_platillo categoria cliente'.split()
    integers='venta_id orden_id anio mes trimestre dia_semana hora sucursal_id platillo_id cliente_id cantidad'.split()
    columns=[{'name':n,'dataType':t,'sourceColumn':n,'summarizeBy':'none'} for t,items in [
        ('string',strings),('int64',integers),('dateTime',['fecha']),('boolean',['cliente_identificado']),('decimal',['precio_unitario','importe'])] for n in items]
    for c in columns:
        if c['name']=='nombre_mes':c['sortByColumn']='mes'
        if c['name']=='nombre_dia':c['sortByColumn']='dia_semana'
        if c['name']=='fecha':c['formatString']='dd/MM/yyyy'
        if c['name'] in integers and c['name'].endswith('_id'):c['isHidden']=True
    query=['let','    Fuente = PostgreSQL.Database(Servidor, BaseDatos, [CreateNavigationProperties=false]),',
           '    Ventas = Fuente{[Schema="datamart",Item="v_ventas_analisis"]}[Data],',
           '    Tipos = Table.TransformColumnTypes(Ventas, {{"fecha", type date}, {"importe", Currency.Type}, {"precio_unitario", Currency.Type}})',
           'in','    Tipos']
    save(MODEL/'definition.pbism',{'version':'1.0','settings':{}})
    save(MODEL/'model.bim',{'name':'Aurea','compatibilityLevel':1600,'model':{
        'culture':'es-GT','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'es-GT',
        'expressions':[{'name':'Servidor','kind':'m','expression':'"localhost:5432" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
                       {'name':'BaseDatos','kind':'m','expression':'"PRF_Aurea_OLAP" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
        'tables':[{'name':'Ventas','columns':columns,
           'measures':[{'name':n,'expression':e,'formatString':f,'displayFolder':'Indicadores'} for n,e,f in measures],
           'partitions':[{'name':'Ventas','mode':'import','source':{'type':'m','expression':query}}]}],
        'annotations':[{'name':'PBI_QueryOrder','value':'["Servidor","BaseDatos","Ventas"]'}]}})
    save(ROOT/'Aurea.pbip',{'version':'1.0','artifacts':[{'report':{'path':'Aurea.Report'}}],'settings':{'enableAutoRecovery':True}})
    save(REPORT/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json',
        'version':'4.0','datasetReference':{'byPath':{'path':'../Aurea.SemanticModel'}}})
    save(REPORT/'definition/version.json',{'$schema':BASE+'versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    save(REPORT/'definition/report.json',{'$schema':BASE+'report/2.0.0/schema.json',
        'themeCollection':{'customTheme':{'name':'tema_aurea.json','reportVersionAtImport':'5.56','type':'RegisteredResources'}},
        'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources',
            'items':[{'name':'tema_aurea.json','path':'tema_aurea.json','type':'CustomTheme'}]}]})
    save(REPORT/'definition/pages/pages.json',{'$schema':BASE+'pagesMetadata/1.0.0/schema.json',
        'pageOrder':['resumen','productos','simulados'],'activePageName':'resumen'})
    for name,title,source in [('resumen','01 · Resumen ejecutivo','Proyecto 2'),('simulados','03 · Escenario simulado','Simulado SQL')]:
        page(name,title,source)
        for i,m in enumerate(['Ventas Q','Compras','Unidades','Ticket promedio Q']):
            visual(name,'kpi'+str(i),'card',m,(24+i*312,208,296,92),{'Values':[(m,True)]},objects={
                'labels':[{'properties':{'labelDisplayUnits':literal(0),'fontSize':literal(28),'color':color('#203B35')}}],
                'categoryLabels':[{'properties':{'show':literal(False)}}]})
        visual(name,'tendencia','lineChart','Evolución diaria · Q',(24,316,720,250),{'Category':[('fecha',False)],'Y':[('Ventas Q',True)]},('fecha',False,'Ascending'))
        visual(name,'sucursales','clusteredBarChart','Ventas por sucursal · Q',(760,316,496,250),{'Category':[('nombre_sucursal',False)],'Y':[('Ventas Q',True)]},('Ventas Q',True,'Descending'))
        visual(name,'categorias','donutChart','Participación por categoría · Q',(24,582,510,250),{'Category':[('categoria',False)],'Y':[('Ventas Q',True)]})
        visual(name,'horas','clusteredColumnChart','Compras por hora local',(550,582,706,250),{'Category':[('hora',False)],'Y':[('Compras',True)]},('hora',False,'Ascending'))
        note='Datos simulados: repetición de patrones del Proyecto 2. No representan demanda observada ni pronósticos.' if source=='Simulado SQL' else 'Proyecto 2: 15 oct - 05 nov 2026. Sin datos de costos: ventas no equivalen a utilidad.'
        text(name,'nota',note,(24,846,1232,38),11)
    page('productos','02 · Portafolio y decisiones','Proyecto 2')
    visual('productos','mezcla','treemap','Composición de ventas por categoría y platillo',(24,212,610,290),{'Group':[('categoria',False)],'Details':[('nombre_platillo',False)],'Values':[('Ventas Q',True)]})
    visual('productos','dispersion','scatterChart','Productos · volumen frente a precio medio',(650,212,606,290),{'Category':[('nombre_platillo',False)],'X':[('Unidades',True)],'Y':[('Precio medio Q',True)],'Size':[('Ventas Q',True)]})
    visual('productos','ranking','clusteredBarChart','Ventas por platillo · Q',(24,518,760,320),{'Category':[('nombre_platillo',False)],'Y':[('Ventas Q',True)]},('Ventas Q',True,'Descending'))
    text('productos','decision','DECISIONES A VALIDAR\n\n1. Priorizar disponibilidad de productos con mayor venta.\n\n2. Probar venta cruzada en categorías complementarias.\n\n3. Ajustar turnos según compras por hora.\n\nMedir resultados con un piloto; no inferir rentabilidad sin costos.',(800,518,456,320),15)
    text('productos','nota','El filtro de categoría afecta el ticket: incluye solo los importes de las líneas seleccionadas.',(24,846,1232,38),11)
    save(ROOT/'tema_aurea.json',{'name':'Áurea · Verde y oro','dataColors':['#235347','#C49A50','#748B6F','#B87351','#596C8C','#B9A88C'],
       'background':'#F3F0E8','foreground':'#203B35','tableAccent':'#C49A50'})
    save(REPORT/'StaticResources/RegisteredResources/tema_aurea.json',json.loads((ROOT/'tema_aurea.json').read_text(encoding='utf-8')))
    (ROOT/'medidas.dax').write_text('\n\n'.join(n+' = '+e for n,e,f in measures),encoding='utf-8')
    print('Proyecto PBIP generado: '+str(ROOT/'Aurea.pbip'))


if __name__=='__main__':main()
