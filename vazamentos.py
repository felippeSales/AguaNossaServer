# -*- coding: utf-8 -*-
from util import find_index, geocode, cep_to_address, build_complete_address
import urllib  
import cgi
import json
import gspread
import util
from oauth2client.client import SignedJwtAssertionCredentials

vazamentos = []
planilha_vazamentos = None

ADDRESS_VAZAMENTOS_HEADER = 'Nome da rua:'.decode('utf-8')
DISTRICT_VAZAMENTOS_HEADER = 'Bairro:'.decode('utf-8')
CITY_VAZAMENTOS_HEADER = 'Cidade:'.decode('utf-8')
STATE_VAZAMENTOS_HEADER = 'Estado:'.decode('utf-8')
LAT_LNG_VAZAMENTOS_HEADER = 'Latitude / Longitude'.decode('utf-8')

def ler_planilha():
    global planilha_vazamentos
    json_key = json.load(open('vazamentosCredentials.json'))  
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
    gc = gspread.authorize(credentials)
  
    sht1 = gc.open_by_key("1qsKCfX99CCUJ33tflWgAVzneNYaPVwNnuVJIel3cB5Q")

    planilha_vazamentos = sht1.get_worksheet(0)
    return planilha_vazamentos

def ler_respostas():
    planilha_vazamentos = ler_planilha()
    linhas = planilha_vazamentos.get_all_values()
    indice = len(vazamentos) + 1
    
    for i in range(indice, len(linhas)):
        vazamento = processa_linha(linhas[i], i+1)
        vazamentos.append(vazamento)

def processa_linha(linha, indice_linha):
    vazamento = dict(address = linha[ADDRESS_VAZAMENTOS_INDEX], district = linha[DISTRICT_VAZAMENTOS_INDEX], state = linha[STATE_VAZAMENTOS_INDEX],city = linha[CITY_VAZAMENTOS_INDEX], lat_lng = linha[LAT_LNG_VAZAMENTOS_INDEX] )
    
    if (vazamento['city'] != 'Desconhecida' and vazamento['lat_lng'] == ''):
        print(monta_endereco(vazamento))   
        address_geocode = geocode(monta_endereco(vazamento))
        vazamento['lat_lng'] = address_geocode
        atualiza_celula(indice_linha, LAT_LNG_VAZAMENTOS_INDEX+1, address_geocode)
        
        
def atualiza_celula(row, col, val):
    
    if planilha_vazamentos == None:
        return
    
    planilha_vazamentos.update_cell(row, col, val)
        
def monta_endereco(notification):
    complete_address = ''
    
    if (notification['address'] != ''):
        complete_address += notification['address'] + ','

    if (notification['district'] != ''):
        complete_address += notification['district'] + ','
        
    if (notification['state'] != ''):
        complete_address += notification['state'] + ','
        
    if (notification['city'] != ''):
        complete_address += notification['city']
        
    return complete_address.encode('utf-8')

def start():
    global ADDRESS_VAZAMENTOS_INDEX, DISTRICT_VAZAMENTOS_INDEX, STATE_VAZAMENTOS_INDEX, CITY_VAZAMENTOS_INDEX, LAT_LNG_VAZAMENTOS_INDEX, planilha_vazamentos

    ler_planilha()
    cabecalho = planilha_vazamentos.row_values(1)
    
    ADDRESS_VAZAMENTOS_INDEX = find_index(cabecalho,ADDRESS_VAZAMENTOS_HEADER)
    DISTRICT_VAZAMENTOS_INDEX = find_index(cabecalho,DISTRICT_VAZAMENTOS_HEADER)
    STATE_VAZAMENTOS_INDEX = find_index(cabecalho,STATE_VAZAMENTOS_HEADER)
    CITY_VAZAMENTOS_INDEX = find_index(cabecalho,CITY_VAZAMENTOS_HEADER)
    LAT_LNG_VAZAMENTOS_INDEX = find_index(cabecalho,LAT_LNG_VAZAMENTOS_HEADER)
    
    ler_respostas()
    
    
url = "http://cep.republicavirtual.com.br/web_cep.php?cep=58400-640&formato=query_string"

data = urllib.urlopen(url).read()

result = cgi.parse_qs(data)

result_dict = dict(address='', district='', city='Desconhecida', state='Desconhecido')
    
if result['resultado'][0] == '1':
    result_dict['address'] = result['tipo_logradouro'][0] + ' ' + result['logradouro'][0]
    result_dict['district'] = result['bairro'][0]
    result_dict['city'] = result['cidade'][0]
    result_dict['state'] = result['uf'][0]
elif result['resultado'][0] == '2':
    result_dict['city'] = result['cidade'][0]
    result_dict['state'] = result['uf'][0]
    
print result_dict