"""Documentación PDF y referencia visual. La referencia no reemplaza la exportación de Power BI."""
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
GREEN='#203B35'; GOLD='#B88A3D'; MUTED='#64766D'; CREAM='#F4F1E9'


def para(c,text,x,y,w,size=11,color=GREEN):
    p=Paragraph(text,ParagraphStyle('body',fontName='Helvetica',fontSize=size,leading=size*1.45,textColor=HexColor(color)))
    _,h=p.wrap(w,1000);p.drawOn(c,x,y-h);return y-h-12


def start(c,title,num,kicker='ÁUREA / IMPLEMENTACIÓN OLAP'):
    c.setFillColor(HexColor(CREAM));c.rect(0,0,842,595,fill=1,stroke=0)
    c.setFillColor(HexColor(GOLD));c.rect(36,544,36,4,fill=1,stroke=0)
    c.setFont('Helvetica-Bold',9);c.drawString(84,543,kicker)
    para(c,title,36,519,770,25)
    c.setFillColor(HexColor(MUTED));c.setFont('Helvetica',8)
    c.drawString(36,24,'Proyecto 3 · CC3088 · Fuentes proporcionadas por el equipo · Noviembre 2026')
    c.drawRightString(806,24,str(num))


def box(c,x,y,w,h,title,rows):
    c.setFillColor(white);c.setStrokeColor(HexColor('#D5DCD5'));c.roundRect(x,y,w,h,7,fill=1,stroke=1)
    c.setFillColor(HexColor(GREEN));c.roundRect(x,y+h-31,w,31,7,fill=1,stroke=0)
    c.setFillColor(white);c.setFont('Helvetica-Bold',11);c.drawString(x+12,y+h-20,title)
    yy=y+h-44
    for row in rows:
        c.setFillColor(HexColor(GREEN));c.setFont('Helvetica',9);c.drawString(x+12,yy,row);yy-=14


def document():
    c=canvas.Canvas(str(OUT/'modelo_y_analisis.pdf'),pagesize=(842,595))
    c.setTitle('Áurea · Modelo estrella y análisis de negocio')
    start(c,'Ventas que permiten decidir',1)
    y=para(c,'<b>Propósito.</b> Identificar productos, sucursales y franjas horarias prioritarias para formular acciones comerciales y operativas medibles.',36,460,750,15)
    for x,v,l in [(36,'Q114,258','Importe · Proyecto 2'),(300,'478','Compras distintas'),(564,'Q239.03','Ticket promedio')]:
        c.setFillColor(white);c.roundRect(x,280,242,115,8,fill=1,stroke=0)
        para(c,v,x+18,365,210,28);para(c,l,x+18,316,210,11)
    para(c,'<b>Alcance.</b> 1,563 líneas del Proyecto 2, del 15 de octubre al 5 de noviembre de 2026. El conjunto adicional contiene 6,619 líneas simuladas, del 1 de julio al 30 de septiembre. La procedencia se conserva en cada hecho.',36,245,755,12)
    para(c,'<b>Uso responsable de los resultados.</b> El nombre Proyecto 2 indica su fuente académica. La simulación no demuestra demanda real ni sirve para medir crecimiento frente al conjunto original. Sin costos no se calcula rentabilidad.',36,157,755,12)
    c.showPage()
    start(c,'Modelo estrella · una línea por orden y platillo',2)
    c.setStrokeColor(HexColor(GOLD));c.setLineWidth(2)
    for x1,y1,x2,y2 in [(266,370,316,360),(576,360,618,370),(266,175,316,220),(576,220,618,175)]:
        c.line(x1,y1,x2,y2)
    box(c,36,294,230,171,'dim_fecha · 128 filas',['PK fecha : date','anio, mes, trimestre : integer','nombre_mes : varchar(15)','dia, dia_semana : integer','nombre_dia : varchar(15)','Calendario continuo; ISO día 1–7'])
    box(c,618,324,188,141,'dim_sucursal · 3 filas',['PK sucursal_id : integer','nombre_sucursal : varchar(100)','Una fila por sucursal'])
    box(c,36,91,230,165,'dim_platillo · 21 filas',['PK platillo_id : integer','nombre_platillo : varchar(100)','categoria : varchar(50)','Una fila por platillo'])
    box(c,618,91,188,165,'dim_cliente · 31 filas',['PK cliente_id : integer','etiqueta : varchar(60)','identificado : boolean','0 = Sin identificar','30 clientes identificados'])
    box(c,316,91,260,374,'fact_ventas · 8,182 filas',['PK venta_id : bigint identity','origen_datos : text','orden_id : integer','FK fecha : date','FK sucursal_id : integer','FK platillo_id : integer','FK cliente_id : integer','hora : integer [0–23]','cantidad : integer > 0','precio_unitario : numeric(10,2)','importe : numeric(12,2) >= 0','','UQ (origen_datos, orden_id,','       platillo_id)','','importe = cantidad × precio_unitario'])
    para(c,'Relaciones: cada dimensión 1 → N fact_ventas. Claves naturales en dimensiones; venta_id es clave sustituta. No se implementan dimensiones lentamente cambiantes.',36,71,770,9)
    c.showPage()
    start(c,'Pipeline reproducible y controles',3)
    steps=[('01 / FUENTES','CSV originales en data/. Hash SHA-256 y encabezados verificados; no se alteran los archivos recibidos.'),
           ('02 / STAGING','Dos tablas con diez columnas text. La importación conserva la fuente; se ejecuta dentro de una transacción.'),
           ('03 / LIMPIEZA','TRIM, tipos enteros/decimales, offset a America/Guatemala, nulos de cliente. Se rechazan duplicados, cantidades inválidas y catálogos inconsistentes.'),
           ('04 / ESTRELLA','Calendario completo; carga de dimensiones de ambas fuentes; cliente 0; hechos con unicidad, FK y validación aritmética.'),
           ('05 / ANÁLISIS','v_ventas_analisis une las cinco tablas. Power BI importa la vista y calcula medidas bajo los filtros activos.')]
    y=460
    for title,body in steps:
        para(c,title,36,y,190,12,color=GOLD);para(c,body,236,y,570,11);y-=72
    para(c,'<b>Transacción:</b> cualquier discrepancia revierte la carga. Reejecutar fuentes idénticas no duplica hechos. Cambios a ventas existentes requieren otra base vacía; no se presume una estrategia CDC.',36,87,770,10)
    c.showPage()
    start(c,'Métricas y preguntas de negocio',4)
    rows=[('Ventas Q','SUM(importe)','¿Cuál es el importe bruto de las líneas seleccionadas?'),
          ('Compras','DISTINCTCOUNT(compra_clave)','¿Cuántas órdenes diferentes contienen esas líneas?'),
          ('Unidades','SUM(cantidad)','¿Cuántas unidades se vendieron?'),
          ('Ticket promedio Q','Ventas Q / Compras','¿Cuál es el importe seleccionado por compra?'),
          ('Precio medio Q','Ventas Q / Unidades','¿Cuál es el precio ponderado por unidades?'),
          ('Clientes identificados','DISTINCTCOUNT(cliente_id), identificado=true','¿Cuántos clientes conocidos aparecen en el filtro?')]
    y=458
    for name,formula,question in rows:
        c.setFillColor(white);c.roundRect(36,y-49,770,55,4,fill=1,stroke=0)
        para(c,name,48,y,192,11);para(c,escape(formula),244,y,550,10);para(c,question,244,y-21,550,9,color=MUTED);y-=64
    para(c,'compra_clave = origen_datos + ":" + orden_id. Los conteos distintos y el ticket no se suman entre categorías. Al filtrar una categoría, el ticket corresponde solo a las líneas de esa categoría.',36,65,770,9)
    c.showPage()
    start(c,'Decisiones propuestas · evidencia y medición',5)
    data=json.loads((OUT/'analisis_negocio.json').read_text(encoding='utf-8'))
    cards=[('59.41 % de las compras al mediodía','284 de 478 compras se registran entre las 12:00 y las 13:59.','Probar cobertura y preparación reforzada durante dos semanas. Recoger tiempos de espera y medir compras por hora antes y después.'),
           ('Q12,810 en el producto líder','Pollo en salsa de champiñones: 122 unidades; 11.21 % de las ventas del conjunto Proyecto 2.','Revisar disponibilidad e insumos. Registrar quiebres y desperdicio para decidir compras; estos datos no están en las fuentes.'),
           ('53.75 % del importe en platos fuertes','Q61,410 de Q114,258; bebidas Q40,118 y postres Q12,730.','Probar venta cruzada en una sucursal. Medir ticket y unidades por compra; incorporar costos antes de evaluar margen.')]
    y=460
    for title,evidence,action in cards:
        para(c,title,36,y,770,16);para(c,evidence,36,y-31,770,11);para(c,'<b>Acción y evaluación.</b> '+action,36,y-61,770,11);y-=132
    para(c,'Las propuestas son hipótesis para un piloto. La ventana académica de 22 días y el escenario simulado no permiten inferir causalidad ni estacionalidad anual.',36,61,770,9)
    c.showPage()
    start(c,'Validación, reproducción y entrega',6)
    checks=json.loads((OUT/'pruebas_postgresql.json').read_text(encoding='utf-8'))
    y=460
    for item in checks['comprobaciones']:
        y=para(c,'<b>OK</b>  '+escape(item),36,y,770,11)
    y-=5
    y=para(c,'<b>Reproducir.</b> Crear PRF_Aurea_OLAP vacía. Desde olap: python cargar.py --solo-validar; después ejecutar psql con cargar.psql. Los pasos completos están en README.md.',36,y,770,11)
    y=para(c,'<b>Power BI.</b> Abrir powerbi/Aurea.pbip, configurar Servidor y BaseDatos, autenticar y actualizar. Verificar KPIs, probar filtros y exportar a PDF desde Desktop. El proyecto editable contiene seis tipos de gráficos y páginas separadas por origen.',36,y,770,11)
    y=para(c,'<b>Respaldo.</b> output/aurea_olap.sql se produjo con pg_dump de PostgreSQL 18, sin propietarios ni privilegios. La restauración fue probada sobre otra base vacía. Conservar el código SQL, fuentes, documentación y tablero exportado.',36,y,770,11)
    para(c,'<b>Referencia técnica:</b> Microsoft Learn, Power BI Desktop projects; Project report folder; Project semantic model folder. Enlaces completos en README.md. Requisitos académicos: enunciado Proyecto 03 proporcionado por el usuario.',36,93,770,9)
    c.save()


def reference():
    rows=list(csv.DictReader((ROOT/'data/ventas_aurea_p2.csv').open(encoding='utf-8-sig')))
    daily=defaultdict(float);branches=defaultdict(float);cats=defaultdict(float);hours=defaultdict(set);products=defaultdict(lambda:[0,0])
    for r in rows:
        dt=datetime.fromisoformat(r['fecha_hora']).astimezone(timezone(timedelta(hours=-6)))
        amount=int(r['cantidad'])*float(r['precio_unitario'])
        daily[dt.date()]+=amount;branches[r['nombre_sucursal']]+=amount;cats[r['categoria']]+=amount
        hours[dt.hour].add(r['orden_id']);products[r['nombre_platillo']][0]+=int(r['cantidad']);products[r['nombre_platillo']][1]+=amount
    c=canvas.Canvas(str(OUT/'referencia_tablero.pdf'),pagesize=(842,595))
    c.setTitle('Áurea · Referencia visual; no exportación Power BI')
    start(c,'Resumen ejecutivo · Proyecto 2',1,'ÁUREA / REFERENCIA VISUAL DEL TABLERO')
    for i,(value,label) in enumerate([('Q114,258','Ventas'),('478','Compras'),('2,363','Unidades'),('Q239.03','Ticket')]):
        x=36+i*196;c.setFillColor(white);c.roundRect(x,395,182,77,5,fill=1,stroke=0)
        para(c,value,x+12,453,160,23);para(c,label,x+12,419,160,10)
    def panel(x,y,w,h,title):
        c.setFillColor(white);c.roundRect(x,y,w,h,5,fill=1,stroke=0);para(c,title,x+12,y+h-12,w-24,11)
    panel(36,220,432,162,'Evolución diaria · Q')
    values=sorted(daily.items());mx=max(v for d,v in values)
    pts=[(66+i*370/(len(values)-1),245+v/mx*92) for i,(d,v) in enumerate(values)]
    c.setStrokeColor(HexColor(GREEN));c.setLineWidth(2)
    for a,b in zip(pts,pts[1:]):c.line(*a,*b)
    para(c,'15 oct',52,240,60,8);para(c,'05 nov',405,240,60,8);para(c,'Máximo Q'+format(mx,',.0f'),300,358,150,8)
    panel(482,220,324,162,'Ventas por sucursal · Q')
    for i,(name,val) in enumerate(sorted(branches.items(),key=lambda x:-x[1])):
        yy=326-i*38;para(c,escape(name.replace('Áurea ','')),494,yy+7,90,9)
        c.setFillColor(HexColor(GREEN));c.rect(575,yy-9,val/42000*140,16,fill=1,stroke=0)
        para(c,format(val,',.0f'),725,yy+5,70,9)
    panel(36,58,326,148,'Participación por categoría · Q')
    total=sum(cats.values());angle=90
    palette=[GREEN,GOLD,'#7E9686']
    for i,(name,val) in enumerate(sorted(cats.items(),key=lambda x:-x[1])):
        extent=360*val/total;c.setFillColor(HexColor(palette[i]));c.wedge(53,73,160,180,angle,extent,fill=1,stroke=0);angle+=extent
        para(c,f'{escape(name)} · {val/total:.1%}',177,157-i*29,175,9)
    c.setFillColor(white);c.circle(106.5,126.5,30,fill=1,stroke=0)
    panel(376,58,430,148,'Compras por hora local')
    for i,h in enumerate(range(8,23)):
        val=len(hours[h]);x=397+i*26;c.setFillColor(HexColor(GOLD if h in (12,13) else GREEN));c.rect(x,84,17,val/175*75,fill=1,stroke=0)
        para(c,str(h),x-1,79,25,7)
        if h in (12,13):para(c,str(val),x-1,91+val/175*75,30,7)
    c.setFillColor(HexColor(MUTED));c.setFont('Helvetica',7);c.drawString(36,42,'Referencia calculada desde CSV. Para la entrega académica exportar el tablero nativo desde Power BI Desktop.')
    c.showPage()
    start(c,'Portafolio · volumen, precio y concentración',2,'ÁUREA / REFERENCIA VISUAL DEL TABLERO')
    panel(36,250,380,220,'Dispersión · unidades y precio medio Q')
    c.setStrokeColor(HexColor('#BBC6BF'));c.line(75,284,388,284);c.line(75,284,75,425)
    for name,(qty,amount) in products.items():
        x=84+(qty-90)/40*288;y=289+(amount/qty)/120*132
        c.setFillColor(HexColor(GOLD if amount==max(v[1] for v in products.values()) else GREEN));c.circle(x,y,3+amount/12810*5,fill=1,stroke=0)
    c.setFillColor(HexColor(MUTED));c.setFont('Helvetica',8)
    for tick in [90,100,110,120,130]:c.drawCentredString(84+(tick-90)/40*288,272,str(tick))
    para(c,'Unidades',190,265,100,8)
    para(c,'Q0',40,294,35,8);para(c,'Q120',40,428,35,8)
    panel(432,250,374,220,'Composición del importe · categorías')
    xx=445
    for i,(name,val) in enumerate(sorted(cats.items(),key=lambda x:-x[1])):
        width=348*val/total;c.setFillColor(HexColor(palette[i]));c.rect(xx,274,width-3,147,fill=1,stroke=0)
        para(c,escape(name).replace(' ','<br/>'),xx+4,401,width-9,8,color='#FFFFFF');xx+=width
    panel(36,58,770,178,'Cinco productos con mayor importe · Q')
    for i,(name,(qty,amount)) in enumerate(sorted(products.items(),key=lambda x:-x[1][1])[:5]):
        yy=196-i*27;para(c,escape(name),49,yy+3,260,9)
        c.setFillColor(HexColor(GREEN));c.rect(315,yy-10,amount/12810*380,15,fill=1,stroke=0)
        para(c,'Q'+format(amount,',.0f'),708,yy+3,80,9)
    c.save()


if __name__=='__main__':
    OUT.mkdir(exist_ok=True);document();reference();print('Documentación y referencia visual generadas.')
