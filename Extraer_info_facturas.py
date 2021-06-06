#!/usr/bin/python
import sys
import pdfplumber
import pandas as pd
import re
from os import walk
import os

def get_files_list(path):
    """
    El objetivo de esta función es extraer una lista con todos los ficheros de la carpeta
    especificada, y filtrarla para quedarnos solo con los que acaban en .pdf
    Devuelve una lista con los nombres de todos los ficheros PDF.
    """
    f=[] #crear lista vacía
    os.chdir(path)
    ficheros=pd.DataFrame(os.listdir(),columns=['ficheros']) #pasar la lista a pandas DF
    
    filtro=ficheros['ficheros'].str.contains(".*pdf") #crear filtro para seleccionar PDFs
    ficheros=ficheros[filtro] #seleccionar PDFs del dataframe
    lista_ficheros=ficheros.values.tolist() #pasar el DF a lista
    return lista_ficheros

# Lista de expresiones regulares (patrones) para seleccionar las líneas del PDF:
cups_re=re.compile(r"ES\d{16}[A-Z]")
id_re=re.compile(r"UFGC\d{5}")
transf_re=re.compile(r'Transferencia.*')
total_re=re.compile(r'TOTAL FACTURA.*')
lectura_re=re.compile(r'GU00.*m3.*')
periodo_re=re.compile(r'\d{2}-\d{2}-.*')

def extract_info(path):
    """
    A partir de las expresiones regulares definidas anteriormente,
    esta función parsea todos los PDFs de la carpeta en busca de las 
    líneas que contienen esas expresiones, y extraen la información
    correspondiente de estas líneas.
    Finalmente, crea una lista de diccionarios con la info y la pasa 
    a dataframe de pandas.
    Devuelve un dataframe de pandas con toda la información seleccionada
    de los PDF.
    """
    d = [] #crear lista vacía
    lista_ficheros = get_files_list(path) #obtener lista ficheros PDF
    for file in lista_ficheros: #iterar sobre lista ficheros
        with pdfplumber.open(file[0]) as pdf: #parsear cada PDF
            page=pdf.pages[0] #seleccionar la primera página
            text=page.extract_text() #extraer el texto
            for line in text.split('\n'): #iterar sobre líneas
                for field in line.split(): #iterar sobre campos 
                    if cups_re.match(field): #seleccionar campo con CUPS
                        cups=field #y guardarlo
                if transf_re.match(line): #seleccionar línea con fecha emisión
                    fecha_emision=line.split()[1] #guardar fecha emisión, que se encuentra en segundo campo
                if periodo_re.match(line): #seleccionar campo con fechas periodo
                    fecha_inicio,_,fecha_fin=line.split() #guardar fechas
                if total_re.match(line): #seleccionar línea con importe
                    importe=line.split()[2] #guardar tercer campo
                if lectura_re.match(line): #seleccionar línea con consumo
                    metros_cubicos=line.split()[-3] #guardar tercer campo desde la derecha
                    consumo=line.split()[-1] #guardar último campo
        #añadir diccionarios con todos los campos extraídos a la lista
        d.append(
        {
            'cups':cups,
            'fecha de emisión':fecha_emision,
            'fecha inicio facturación':fecha_inicio,
            'fecha fin facturación':fecha_fin,
            'consumo mensual facturado (kwh)':consumo,
            'Consumo m3':metros_cubicos,
            'importe':importe,
            
            
        })

    ids_cups=pd.DataFrame(d) #crear pandas DF a partir de diccionario
    for col in ids_cups.columns[1:4]:
        ids_cups[col] = pd.to_datetime(ids_cups[col], dayfirst=True).dt.strftime('%d/%m/%Y')
    return ids_cups

def parse_excel(file_name,cups):
    facturas_gas=pd.read_excel(file_name+".xlsx",parse_dates=[2,3,4],engine='openpyxl')
    cups_lista=pd.read_excel(cups)
    diccionario_cups=cups_lista[["NumeroCupsContador","NombreCentro"]].dropna().set_index("NumeroCupsContador").to_dict()['NombreCentro']
    facturas_gas["días"]=facturas_gas["fecha fin facturación"]-facturas_gas["fecha inicio facturación"]
    facturas_gas['consumo mensual facturado (kwh)']=facturas_gas['consumo mensual facturado (kwh)'].str.replace('.','').str.replace(',','.')
    facturas_gas['importe']=facturas_gas['importe'].str.replace('.','').str.replace(',','.')
    facturas_gas["num_días"]=facturas_gas["días"].astype(str).str.split(" ",expand=True)[0]
    facturas_gas["num_días"]=facturas_gas["num_días"].astype(int)
    facturas_gas["consumo_diario"]=facturas_gas["consumo mensual facturado (kwh)"].astype(float)/facturas_gas["num_días"]
    facturas_gas["importe diario"]=facturas_gas["importe"].astype(float)/facturas_gas["num_días"]
    consumo_por_dias=pd.concat([pd.DataFrame({'cups':row['cups'],'centro':diccionario_cups[row['cups']],'importe_diario':row["importe diario"],
                                          'fecha': pd.date_range(row["fecha inicio facturación"],
                                                                 row["fecha fin facturación"]),
                         'consumo_diario':row["consumo_diario"]}) for i,row in facturas_gas.iterrows()],
                           ignore_index=True)
    consumo_por_dias.set_index('fecha',inplace=True)
    consumo_por_mes=consumo_por_dias.groupby([consumo_por_dias.index.year,consumo_por_dias.index.month,
                                          consumo_por_dias.cups,consumo_por_dias.centro]).sum()
    consumo_por_mes.index.rename(["año","mes","cups","centro"],inplace=True)
    consumo_por_mes.columns=['importe_mensual','consumo_mensual']
    consumo_por_mes=consumo_por_mes.round(2)
    consumo_por_mes.to_csv("consumo_por_mes.csv",encoding='utf_8_sig')


    
def df_to_excel(path,file_name,cups):
    """
    Con el dataframe de pandas, esta función genera un fichero excel
    con el nombre que le damos, y la información extraída de los PDF
    de la ruta (path) especificada.
    """
    df = extract_info(path)
    df.to_excel(file_name + ".xlsx")
    parse_excel(file_name,cups)
    

def main(argvs):
    if len(argvs) != 4:
        print("Este script se debe correr así:")
        print("python Extraer_info_facturas.py ruta_PDFs nombre_excel lista_cups")
    else:
        df_to_excel(argvs[1],argvs[2],argvs[3])


if __name__ == "__main__":
    main(sys.argv)
