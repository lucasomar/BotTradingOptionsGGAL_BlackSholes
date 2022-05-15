# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 17:38:09 2021

@author: Lucas
"""

# Bot traiging de tasa con opciones de GGAL
# Comprar a la tasa más alta según el strike y liquidez del mercado
# Sintetico = Strike + precio prima venta Call - precio prima compra put - precio compra accion
# Sintetico desarmado = -Strike - precio prima compra Call + precio prima venta put + precio venta accion


'Señal de compra --> Tasa > 2x tasa caución'
'Señal de venta --> Tasa < 1.25x tasa caución'



# 0) tokens API IOL
import requests
import datetime as dt
import pandas as pd
import math
from datetime import date

'Mostrar todas las filas y columnas del DataFrame'
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def pedirToken():
    url = 'https://api.invertironline.com/token'
    data = {'username':'','password':'','grant_type':'password'}
    r = requests.post(url = url, data = data).json()
    return r


def checkToken(tk):
    exp = dt.datetime.strptime(tk['.expires'],'%a, %d %b %Y %H:%M:%S GMT')
    ahora = dt.datetime.utcnow()
    tiempo = exp-ahora
    return tiempo


def actualizarToken(tk):
    exp = dt.datetime.strptime(tk['.expires'],'%a, %d %b %Y %H:%M:%S GMT')
    ahora = dt.datetime.utcnow()
    tiempo = exp-ahora
    dias = tiempo.days
    
    if checkToken(tk).days == 0:
        tokenOk = tk
    else:
        tokenOk = pedirToken()
        
    return tokenOk


'Usar pedirToken() al comienzo del script y luego actualizarToken()'


# 1) Traer los el panel de precios de GGAL y sus opciones

def titulo(ticker):
    url_base = 'https://api.invertironline.com/api/v2/'
    endpoint = 'bCBA/Titulos/'+ticker
    url = url_base + endpoint
    headers = {'Authorization':'Bearer '+ tk['access_token']}
    
    data = requests.get(url = url, headers = headers).json()
    return data


def opcionesDe(ticker):
    url_base = 'https://api.invertironline.com/api/v2/'
    endpoint = 'bcba/Titulos/'+ticker+'/Opciones'
    url = url_base + endpoint
    headers = {'Authorization':'Bearer '+ tk['access_token']}
    
    data = requests.get(url = url, headers = headers).json()
    
    opciones = []
    for i in range(len(data)):
        opcion = data[i]['cotizacion']
        opcion['simbolo'] = data[i]['simbolo']
        opcion['tipo'] = data[i]['tipoOpcion']
        opcion['vencimiento'] = data[i]['fechaVencimiento']
        opcion['descripcion'] = data[i]['descripcion']
        opciones.append(opcion)
    tabla = pd.DataFrame(opciones).set_index('simbolo')
    return tabla


def precio(ticker):
    url_base = 'https://api.invertironline.com/api/v2/'
    endpoint = 'bcba/Titulos/'+ticker+'/Cotizacion'
    url = url_base + endpoint
    params = {'model.simbolo':ticker,'model.mercado':'bCBA','model.plazo':'t1'}
    headers = {'Authorization':'Bearer '+ tk['access_token']}
    
    data = requests.get(url = url, headers = headers,params=params).json()
    
    return data

'BlackSholes'
# Aproximación por teorema de Taylor a probabilidad normal estándar
def fi(x):
    pi = 3.141592653589793238;
    a1 = 0.319381530;
    a2 = -0.356563782;
    a3 =  1.781477937;
    a4 = -1.821255978;
    a5 = 1.330274429;
    L = abs(x);
    k = 1 / (1+0.2316419*L);
    p = 1-1/pow(2*pi, 0.5)*math.exp(-pow(L, 2)/2)*(a1*k+a2*pow(k,2)+a3*pow(k,3)+a4*pow(k,4)+a5*pow(k,5));
    if (x>=0):
        return p
    else:
        return 1-p
    
def normalInv(x):
    return ((1/math.sqrt(2*math.pi)) * math.exp(-x*x*0.5))

def bs(S0, K, r, T, sigma, q=0, c_p='Call'):
    ret = {}
    if c_p == 'Call':
        if (S0 > 0 and K > 0 and r >= 0 and T > 0 and sigma > 0):
            d1 = (math.log(S0/K) + (r -q+sigma*sigma*0.5)*T ) / (sigma * math.sqrt(T))
            d2 = d1 - sigma*math.sqrt(T)
            ret['prima'] = math.exp(-q*T) * S0 * fi(d1) - K*math.exp(-r*T)*fi(d2)
            ret['delta'] = math.exp(-q*T) * fi(d1)
            ret['gamma'] = (normalInv(d1) * math.exp(-q*T)) / (S0 * sigma * math.sqrt(T))
            ret['vega'] = 0.01 * S0 * math.exp(-q*T) * normalInv(d1) * math.sqrt(T)
            ret['theta'] = (1/365) * (-((S0*sigma*math.exp(-q*T))/(2*math.sqrt(T))) * normalInv(d1)
                                      - r*K*(math.exp(-r*T))*fi(d2) + q*S0*(math.exp(-q*T)) * fi(d1))
            ret['rho'] = 0.01 * K * T * math.exp(-r*T) * fi(d2)
        else:
            ret['errores'] = 'Se ingresaron valores incorrectos'
    else:
        if (S0 > 0 and K > 0 and r >= 0 and T > 0 and sigma > 0):
            d1 = (math.log(S0/K) + (r -q+sigma*sigma*0.5)*T ) / (sigma * math.sqrt(T))
            d2 = d1 - sigma*math.sqrt(T)
            ret['prima'] = K*math.exp(-r*T) * fi(-d2) - math.exp(-q*T) * S0 * fi(-d1)
            ret['delta'] = math.exp(-q*T) * fi(-d1)
            ret['gamma'] = (normalInv(d1) * math.exp(-q*T)) / (S0 * sigma * math.sqrt(T))
            ret['vega'] = 0.01 * S0 * math.exp(-q*T) * normalInv(d1) * math.sqrt(T)
            ret['theta'] = (1/365) * (-((S0*sigma*math.exp(-q*T))/(2*math.sqrt(T))) * normalInv(d1) 
                                      - r*K*(math.exp(-r*T))*fi(-d2) - q*S0*(math.exp(-q*T)) * fi(-d1))
            ret['rho'] = -0.01 * K * T * math.exp(-r*T) * fi(-d2)
        else:
            ret['errores'] = 'Se ingresaron valores incorrectos'
    return ret

# Función iteración para volatilidad implícita
def vi(S0, K, r, T, prima, q=0, c_p='Call'):
    if (S0 > 0 and K > 0 and r >= 0 and T > 0):
        maximasIteraciones = 300
        pr_techo = prima
        pr_piso = prima
        vi_piso = maximasIteraciones
        vi = maximasIteraciones
        for number in range(1,maximasIteraciones):
            sigma = (number)/100
            primaCalc = bs(S0, K, r, T, sigma,q, c_p=c_p)['prima']
            if primaCalc > prima:
                vi_piso = number -1
                pr_techo = primaCalc
                break
            else:
                pr_piso = primaCalc
                
        rango = (prima - pr_piso) / (pr_techo - pr_piso)
        vi = vi_piso + rango
    else:
        print ("No se puede calcular VI porque los valores ingresados son incorrectos")
    return(vi)



####################################################################################
'Data análisis'

ticker = 'GGAL'
tk = pedirToken()
tk = actualizarToken(tk)
data = opcionesDe(ticker)
#data.to_excel('opcionesDeGGAL.xlsx')


# 2) Armar los sintéticos calculando sus tasas

tickers = ['GFGV170.FE','GFGC170.FE','GFGV175.FE','GFGC175.FE','GFGV180.FE','GFGC180.FE','GFGV185.FE','GFGC185.FE','GFGV190.FE','GFGC190.FE','GFGV195.FE','GFGC195.FE','GFGV200.FE','GFGC200.FE','GFGV210.FE','GFGC210.FE','GFGV220.FE','GFGC220.FE','GFGV230.FE','GFGC230.FE','GFGV240.FE','GFGC240.FE','GFGV250.FE','GFGC250.FE','GFGV260.FE','GFGC260.FE']

c_p = []
for ticker in tickers:
    if 'C' in ticker:
        c_p.append('Call')
    if 'V' in ticker:
        c_p.append('Put')
    else:
        pass

strike = []
for ticker in tickers:
    S = int("".join([x for x in ticker if x.isdigit()]))
    strike.append(S)

dicNuevo = {}
for ticker in tickers:
    try:
        data = precio(ticker)
        dicNuevo[ticker] = data['ultimoPrecio']
    except:
        pass

symbol = list(dicNuevo.keys())
ultimoPrecio = list(dicNuevo.values())
tabla = pd.DataFrame()
tabla['symbol'] = symbol
tabla['ultimoPrecio'] = ultimoPrecio
tabla['c_p'] = c_p
tabla['strike'] = strike



'Hasta acá logré obtener una tabla con los ultimos precios de las opciones de GGAL y de GGAL'

# lo que tengo que hacer es agregar a la tabla la volatilidad implicita de cada ticker en base al spot actual
           

def diasVto():
    d0 = date.today()
    d1 = date(2022, 2, 18)
    delta = d1 - d0
    return(delta.days)

def precioSpot():
    data = precio('GGAL')
    return data['ultimoPrecio']

VI = []
for i in range(len(tabla)):
    S0=201
    K=tabla['strike'][i]
    r=0.5/365
    T=diasVto()/365
    prima=tabla['ultimoPrecio'][i]
    c_p=tabla['c_p'][i]
    volimp = vi(S0, K, r, T, prima, q=0, c_p=c_p)
    VI.append(volimp)

tabla['vi'] = VI

print(tabla)

# para cada cuña graficar:
# eje Z = precio prima
# eje X = vi
# eje Y = spot


#cuna = tabla.loc[12:13]
#K = 200
#primasC = []
#primasP = []
#spots = []
#sigmas = []
#for S0 in range(int(round(S0*0.6,0)),int(round(S0*1.4,0)),1):
#    spots.append(S0)
#    for sigma in range(1,100,5):
#        sigmas.append(sigma)
#        primaCall = bs(S0, K, r, T, sigma/100, q=0, c_p='Call')
#        primasC.append(primaCall['prima'])
#        primaPut = bs(S0, K, r, T, sigma/100, q=0, c_p='Put')
#        primasP.append(primaPut['prima'])

#valores = pd.DataFrame()
#valores['sigmas'] = sigmas
#valores['spots'] = [69,69,69,69,69,69,69,69,69,69,69,69,69,69,69,69,69,69,69,69,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,71,71,71,71,71,71,71,71,71,71,71,71,71,71,71,71,71,71,71,71,72,72,72,72,72,72,72,72,72,72,72,72,72,72,72,72,72,72,72,72,73,73,73,73,73,73,73,73,73,73,73,73,73,73,73,73,73,73,73,73,74,74,74,74,74,74,74,74,74,74,74,74,74,74,74,74,74,74,74,74,75,75,75,75,75,75,75,75,75,75,75,75,75,75,75,75,75,75,75,75,76,76,76,76,76,76,76,76,76,76,76,76,76,76,76,76,76,76,76,76,77,77,77,77,77,77,77,77,77,77,77,77,77,77,77,77,77,77,77,77,78,78,78,78,78,78,78,78,78,78,78,78,78,78,78,78,78,78,78,78,79,79,79,79,79,79,79,79,79,79,79,79,79,79,79,79,79,79,79,79,80,80,80,80,80,80,80,80,80,80,80,80,80,80,80,80,80,80,80,80,81,81,81,81,81,81,81,81,81,81,81,81,81,81,81,81,81,81,81,81,82,82,82,82,82,82,82,82,82,82,82,82,82,82,82,82,82,82,82,82,83,83,83,83,83,83,83,83,83,83,83,83,83,83,83,83,83,83,83,83,84,84,84,84,84,84,84,84,84,84,84,84,84,84,84,84,84,84,84,84,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,86,86,86,86,86,86,86,86,86,86,86,86,86,86,86,86,86,86,86,86,87,87,87,87,87,87,87,87,87,87,87,87,87,87,87,87,87,87,87,87,88,88,88,88,88,88,88,88,88,88,88,88,88,88,88,88,88,88,88,88,89,89,89,89,89,89,89,89,89,89,89,89,89,89,89,89,89,89,89,89,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,90,91,91,91,91,91,91,91,91,91,91,91,91,91,91,91,91,91,91,91,91,92,92,92,92,92,92,92,92,92,92,92,92,92,92,92,92,92,92,92,92,93,93,93,93,93,93,93,93,93,93,93,93,93,93,93,93,93,93,93,93,94,94,94,94,94,94,94,94,94,94,94,94,94,94,94,94,94,94,94,94,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,96,96,96,96,96,96,96,96,96,96,96,96,96,96,96,96,96,96,96,96,97,97,97,97,97,97,97,97,97,97,97,97,97,97,97,97,97,97,97,97,98,98,98,98,98,98,98,98,98,98,98,98,98,98,98,98,98,98,98,98,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,101,102,102,102,102,102,102,102,102,102,102,102,102,102,102,102,102,102,102,102,102,103,103,103,103,103,103,103,103,103,103,103,103,103,103,103,103,103,103,103,103,104,104,104,104,104,104,104,104,104,104,104,104,104,104,104,104,104,104,104,104,105,105,105,105,105,105,105,105,105,105,105,105,105,105,105,105,105,105,105,105,106,106,106,106,106,106,106,106,106,106,106,106,106,106,106,106,106,106,106,106,107,107,107,107,107,107,107,107,107,107,107,107,107,107,107,107,107,107,107,107,108,108,108,108,108,108,108,108,108,108,108,108,108,108,108,108,108,108,108,108,109,109,109,109,109,109,109,109,109,109,109,109,109,109,109,109,109,109,109,109,110,110,110,110,110,110,110,110,110,110,110,110,110,110,110,110,110,110,110,110,111,111,111,111,111,111,111,111,111,111,111,111,111,111,111,111,111,111,111,111,112,112,112,112,112,112,112,112,112,112,112,112,112,112,112,112,112,112,112,112,113,113,113,113,113,113,113,113,113,113,113,113,113,113,113,113,113,113,113,113,114,114,114,114,114,114,114,114,114,114,114,114,114,114,114,114,114,114,114,114,115,115,115,115,115,115,115,115,115,115,115,115,115,115,115,115,115,115,115,115,116,116,116,116,116,116,116,116,116,116,116,116,116,116,116,116,116,116,116,116,117,117,117,117,117,117,117,117,117,117,117,117,117,117,117,117,117,117,117,117,118,118,118,118,118,118,118,118,118,118,118,118,118,118,118,118,118,118,118,118,119,119,119,119,119,119,119,119,119,119,119,119,119,119,119,119,119,119,119,119,120,120,120,120,120,120,120,120,120,120,120,120,120,120,120,120,120,120,120,120,121,121,121,121,121,121,121,121,121,121,121,121,121,121,121,121,121,121,121,121,122,122,122,122,122,122,122,122,122,122,122,122,122,122,122,122,122,122,122,122,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,124,124,124,124,124,124,124,124,124,124,124,124,124,124,124,124,124,124,124,124,125,125,125,125,125,125,125,125,125,125,125,125,125,125,125,125,125,125,125,125,126,126,126,126,126,126,126,126,126,126,126,126,126,126,126,126,126,126,126,126,127,127,127,127,127,127,127,127,127,127,127,127,127,127,127,127,127,127,127,127,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,130,130,130,130,130,130,130,130,130,130,130,130,130,130,130,130,130,130,130,130,131,131,131,131,131,131,131,131,131,131,131,131,131,131,131,131,131,131,131,131,132,132,132,132,132,132,132,132,132,132,132,132,132,132,132,132,132,132,132,132,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,134,134,134,134,134,134,134,134,134,134,134,134,134,134,134,134,134,134,134,134,135,135,135,135,135,135,135,135,135,135,135,135,135,135,135,135,135,135,135,135,136,136,136,136,136,136,136,136,136,136,136,136,136,136,136,136,136,136,136,136,137,137,137,137,137,137,137,137,137,137,137,137,137,137,137,137,137,137,137,137,138,138,138,138,138,138,138,138,138,138,138,138,138,138,138,138,138,138,138,138,139,139,139,139,139,139,139,139,139,139,139,139,139,139,139,139,139,139,139,139,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,140,141,141,141,141,141,141,141,141,141,141,141,141,141,141,141,141,141,141,141,141,142,142,142,142,142,142,142,142,142,142,142,142,142,142,142,142,142,142,142,142,143,143,143,143,143,143,143,143,143,143,143,143,143,143,143,143,143,143,143,143,144,144,144,144,144,144,144,144,144,144,144,144,144,144,144,144,144,144,144,144,145,145,145,145,145,145,145,145,145,145,145,145,145,145,145,145,145,145,145,145,146,146,146,146,146,146,146,146,146,146,146,146,146,146,146,146,146,146,146,146,147,147,147,147,147,147,147,147,147,147,147,147,147,147,147,147,147,147,147,147,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,148,149,149,149,149,149,149,149,149,149,149,149,149,149,149,149,149,149,149,149,149,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,150,151,151,151,151,151,151,151,151,151,151,151,151,151,151,151,151,151,151,151,151,152,152,152,152,152,152,152,152,152,152,152,152,152,152,152,152,152,152,152,152,153,153,153,153,153,153,153,153,153,153,153,153,153,153,153,153,153,153,153,153,154,154,154,154,154,154,154,154,154,154,154,154,154,154,154,154,154,154,154,154,155,155,155,155,155,155,155,155,155,155,155,155,155,155,155,155,155,155,155,155,156,156,156,156,156,156,156,156,156,156,156,156,156,156,156,156,156,156,156,156,157,157,157,157,157,157,157,157,157,157,157,157,157,157,157,157,157,157,157,157,158,158,158,158,158,158,158,158,158,158,158,158,158,158,158,158,158,158,158,158,159,159,159,159,159,159,159,159,159,159,159,159,159,159,159,159,159,159,159,159,160,160,160,160,160,160,160,160,160,160,160,160,160,160,160,160,160,160,160,160]
#valores['primasC'] = primasC
#valores['primasP'] = primasP
#print(valores)

K = 210
sigma = 0.5
precio = bs(210, K, r, T, sigma, q=0, c_p='Call')
