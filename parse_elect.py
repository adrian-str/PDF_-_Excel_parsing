import pandas as pd
import os

os.chdir('./horario')
lista_ficheros=os.listdir()
lista_ficheros

for i,fichero in enumerate(lista_ficheros):
    f1_elect=pd.read_excel(fichero,parse_dates=['fecha'])
    f1_elect=f1_elect.sort_index(axis=1)
    f1_elect.set_index('fecha',inplace=True)
    f1_elect=f1_elect.apply(lambda x: x.str.replace(',','.'))
    f1_elect=f1_elect.astype(float)
    f=pd.DataFrame(f1_elect.groupby([f1_elect.index.year,f1_elect.index.month,f1_elect.index.day]).sum())
    f.index.rename(['año','mes','día'],inplace=True)
    f.reset_index(inplace=True)

    if i==0:
        df=f
    else:
        df=pd.concat([df,f],axis=0,ignore_index=True)

final_df=df.groupby(['año','mes','día']).sum().reset_index().melt(id_vars=["año", "mes","día"], 
        var_name="CUPS", 
        value_name="consumo")

final_df.CUPS=final_df['CUPS'].str.split().str[0]

lista_cups=pd.read_excel('../04-Reparto_CUPS_Centros.xlsx')
lista_cups
diccionario_cups=lista_cups[["NumeroCupsContador","NombreCentro"]].dropna().set_index("NumeroCupsContador").to_dict()['NombreCentro']

consumo_por_dia=pd.concat([pd.DataFrame({'año':row['año'],'mes':row['mes'],'día':row['día'],'cups':row['CUPS'],'centro':diccionario_cups[row['CUPS']],
                         'consumo_diario':row['consumo']},index=[0]) for i,row in final_df.iterrows()],
                           ignore_index=True)

consumo_por_dia.to_csv('../cons_x_día_elect.csv',encoding='utf_8_sig')
