import pandas as pd
import os
import sys

print(sys.argv[0])
print(sys.argv[1])

if len(sys.argv)!=3:
    print("Este contiene un número de argumentos= ", len(sys.argv))
    print("Correr este script así:")
    print("python parse_excel.py excel_factura excel_cups")
    sys.exit()
# la localización de los excel de entrada se la damos a través del comando que ejecuta el script
enertika=sys.argv[0]
# primero el excel de las facturas y después el de los CUPS.
cups=sys.argv[1]
# parseamos los excel en un dataframe de pandas
facturas_gas=pd.read_excel(enertika, engine='openpyxl') 
cups_lista=pd.read_excel(cups, engine='openpyxl')
# pasamos el excel de los CUPS a un diccionario de Python, para poder obtener el nombre del centro a partir del CUPS
diccionario_cups=cups_lista[["NumeroCupsContador","NombreCentro"]].dropna().set_index("NumeroCupsContador").to_dict()['NombreCentro']
# sacamos el numero de días restando la fecha final menos la inicial
facturas_gas["días"]=facturas_gas["fecha fin facturación"]-facturas_gas["fecha inicio facturación"]
# separamos el número de días de la palabra "days"
facturas_gas["num_días"]=facturas_gas["días"].astype(str).str.split(" ",expand=True)[0]
# indicamos que el número de días debe ser tratado como número entero para poder hacer operaciones 
facturas_gas["num_días"]=facturas_gas["num_días"].astype(int)
# sacamos el consumo diario dividiendo el consumo mensual por el número de días
facturas_gas["consumo_diario"]=facturas_gas["consumo mensual facturado (kwh)"]/facturas_gas["num_días"]
# obtenemos el importe diario de la misma forma
facturas_gas["importe diario"]=facturas_gas["Importe cobrado (€)"]/facturas_gas["num_días"]

# unimos la información de interés (CUPS, nombre centro, importe diario, *fechas y consumo diario) en una nueva tabla
"""
para sacar el consumo diario por cada fecha concreta, procesamos cada fila de forma independiente, expandiendo el rango de fechas
y asignando a cada fecha sus datos correspondientes

""" 
consumo_por_dias=pd.concat([pd.DataFrame({'cups':row['cups'],'centro':diccionario_cups[row['cups']],'importe_diario':row["importe diario"],
                                          'fecha': pd.date_range(row["fecha inicio facturación"],
                                                                 row["fecha fin facturación"]),
                         'consumo_diario':row["consumo_diario"]}) for i,row in facturas_gas.iterrows()],
                           ignore_index=True)
# ponemos la fecha como índice para poder agrupar por esta
consumo_por_dias.set_index('fecha',inplace=True)
# para obtener el consumo mensual por centro, agrupamos el consumo e importe por año, mes, centro y CUPS, obteniendo la suma de estos.
consumo_por_mes=consumo_por_dias.groupby([consumo_por_dias.index.year,consumo_por_dias.index.month,
                                          consumo_por_dias.centro,consumo_por_dias.cups]).sum()
# renombramos los índices con los títulos adecuados
consumo_por_mes.index.rename(["año","mes","centro","cups"],inplace=True)
# renombramos las columnas
consumo_por_mes.columns=['importe_mensual','consumo_mensual']
# redondeamos a dos decimales
consumo_por_mes=consumo_por_mes.round(2)
# sacamos un csv a partir de estos datos, con codificación especial para los acentos y la 'ñ'.
consumo_por_mes.to_csv("consumo_por_mes.csv",encoding='utf_8_sig')
