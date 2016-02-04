# -*- coding: utf-8 -*-
from flask import Flask, make_response, request, Response
from util import find_index, geocode, cep_to_address, build_complete_address
import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from threading import Thread
import time
from volumeBoqueirao import read_link, get_volume
import os

notifications = []
worksheet = None

volume = None

ADDRESS_HEADER = 'Nome da rua:'.decode('utf-8')
CEP_HEADER = 'CEP:'.decode('utf-8')
NUMBER_HEADER = 'Número:'.decode('utf-8')
NUMBER_FOR_CEP_HEADER = 'Número do domicílio:'.decode('utf-8') # Número do domicílio - quando tem CEP
DISTRICT_HEADER = 'Bairro:'.decode('utf-8')
CITY_HEADER = 'Cidade:'.decode('utf-8')
STATE_HEADER = 'Estado:'.decode('utf-8')
LAT_LNG_HEADER = 'Latitude / Longitude'.decode('utf-8')

vazamentos = []
planilha_vazamentos = None

ADDRESS_VAZAMENTOS_HEADER = 'Nome da rua:'.decode('utf-8')
DISTRICT_VAZAMENTOS_HEADER = 'Bairro:'.decode('utf-8')
CITY_VAZAMENTOS_HEADER = 'Cidade:'.decode('utf-8')
STATE_VAZAMENTOS_HEADER = 'Estado:'.decode('utf-8')
LAT_LNG_VAZAMENTOS_HEADER = 'Latitude / Longitude'.decode('utf-8')

UPDATE_TIME = 2 # seconds

def setup(app):
    global ADDRESS_INDEX, CEP_INDEX, NUMBER_INDEX, NUMBER_FOR_CEP_INDEX, DISTRICT_INDEX, STATE_INDEX, CITY_INDEX, LAT_LNG_INDEX, ADDRESS_VAZAMENTOS_INDEX, DISTRICT_VAZAMENTOS_INDEX, STATE_VAZAMENTOS_INDEX, CITY_VAZAMENTOS_INDEX, LAT_LNG_VAZAMENTOS_INDEX, planilha_vazamentos, worksheet
    
    configure_app(app)
    worksheet = read_worksheet()    
    headers = worksheet.row_values(1)
    ADDRESS_INDEX = find_index(headers, ADDRESS_HEADER)
    CEP_INDEX = find_index(headers, CEP_HEADER)
    NUMBER_INDEX = find_index(headers, NUMBER_HEADER)
    NUMBER_FOR_CEP_INDEX = find_index(headers, NUMBER_FOR_CEP_HEADER)
    DISTRICT_INDEX = find_index(headers, DISTRICT_HEADER)
    STATE_INDEX = find_index(headers, STATE_HEADER)
    CITY_INDEX = find_index(headers, CITY_HEADER)
    LAT_LNG_INDEX = find_index(headers, LAT_LNG_HEADER)  
    
    planilha_vazamentos = ler_planilha()
    cabecalho = planilha_vazamentos.row_values(1)
    
    ADDRESS_VAZAMENTOS_INDEX = find_index(cabecalho,ADDRESS_VAZAMENTOS_HEADER)
    DISTRICT_VAZAMENTOS_INDEX = find_index(cabecalho,DISTRICT_VAZAMENTOS_HEADER)
    STATE_VAZAMENTOS_INDEX = find_index(cabecalho,STATE_VAZAMENTOS_HEADER)
    CITY_VAZAMENTOS_INDEX = find_index(cabecalho,CITY_VAZAMENTOS_HEADER)
    LAT_LNG_VAZAMENTOS_INDEX = find_index(cabecalho,LAT_LNG_VAZAMENTOS_HEADER)
    
    t = Thread(target=notification_thread)
    t.start()
    return

def configure_app(app):
    here = os.path.abspath(__file__)
    config_path = os.path.join(os.path.dirname(here), 'settings_local.py')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)

def read_worksheet():
    global app, worksheet
    json_key = json.load(open(app.config['GOOGLE_JSON_URL']))   
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
    gc = gspread.authorize(credentials)
    #worksheet = gc.open("1Y4RXKYvdFKCtf6RMyQCjSS7iN-5AfyedfTbJa_vDO5g").sheet1
    #gc = gspread.login(app.config['GOOGLE_EMAIL'], app.config['GOOGLE_PASSWORD'])
    sht1 = gc.open_by_key(app.config['GOOGLE_DRIVE_SHEET_ID'])
    worksheet = sht1.get_worksheet(0)
    return worksheet


def notification_thread():
    while True:
        try:
            ler_respostas()
            retrieve_notifications()
            get_volume_aesa()
        except Exception as e:
            print('Error %s' % e)
        finally:
            time.sleep(UPDATE_TIME)

def retrieve_notifications():
    global worksheet, notifications
    worksheet = read_worksheet()
    rows = worksheet.get_all_values()
    current_index  = len(notifications) + 1
    
    for i in range(current_index, len(rows)):
        notification = process_worksheet_row(rows[i], i+1)
        notifications.append(notification)
       
       

def ler_respostas():
    global planilha_vazamentos, vazamentos
    planilha_vazamentos = ler_planilha()
    linhas = planilha_vazamentos.get_all_values()
    indice = len(vazamentos) + 1
    
    for i in range(indice, len(linhas)):
        vazamento = processa_linha(linhas[i], i+1)
        vazamentos.append(vazamento)


def process_worksheet_row(row, worksheet_row_index):
    
    notification = dict(address = row[ADDRESS_INDEX], city = row[CITY_INDEX], lat_lng = row[LAT_LNG_INDEX], number = row[NUMBER_INDEX], number_for_cep= row[NUMBER_FOR_CEP_INDEX],  district = row[DISTRICT_INDEX], state = row[STATE_INDEX], cep = row[CEP_INDEX])
    
    if (notification['city'] == '' and notification['cep'] != ''):
        address_dict = cep_to_address(notification['cep'])
        notification['address'] = address_dict['address']
        notification['district'] = address_dict['district']
        notification['city'] = address_dict['city']
        notification['state'] = address_dict['state']
        
        update_cell(worksheet_row_index, ADDRESS_INDEX+1, notification['address'])
        update_cell(worksheet_row_index, DISTRICT_INDEX+1, notification['district'])
        update_cell(worksheet_row_index, CITY_INDEX+1, notification['city'])
        update_cell(worksheet_row_index, STATE_INDEX+1, notification['state'])
        
        if (notification['city'] == 'Desconhecida'):
            return
    
   
    if (notification['city'] != 'Desconhecida' and notification['lat_lng'] == ''):
        address_geocode = geocode(build_complete_address(notification))
        
        notification['lat_lng'] = address_geocode
        update_cell(worksheet_row_index, LAT_LNG_INDEX+1, address_geocode)
     
    return notification

def update_cell(row, col, val):
    if worksheet == None:
        return
    worksheet.update_cell(row, col, val)

def ler_planilha():
    global planilha_vazamentos
    json_key = json.load(open('/home/aguanossa/vazamentosCredentials.json'))  
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
    gc = gspread.authorize(credentials)
  
    sht1 = gc.open_by_key("1qsKCfX99CCUJ33tflWgAVzneNYaPVwNnuVJIel3cB5Q")

    planilha_vazamentos = sht1.get_worksheet(0)
    return planilha_vazamentos


def processa_linha(linha, indice_linha):
    vazamento = dict(address = linha[ADDRESS_VAZAMENTOS_INDEX], district = linha[DISTRICT_VAZAMENTOS_INDEX], state = linha[STATE_VAZAMENTOS_INDEX],city = linha[CITY_VAZAMENTOS_INDEX], lat_lng = linha[LAT_LNG_VAZAMENTOS_INDEX] )
    
    if (vazamento['city'] != 'Desconhecida' and vazamento['lat_lng'] == ''):
        print(monta_endereco(vazamento))   
        address_geocode = geocode(monta_endereco(vazamento))
        vazamento['lat_lng'] = address_geocode
        atualiza_celula(indice_linha, LAT_LNG_VAZAMENTOS_INDEX+1, address_geocode)
    
    return vazamento
        
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



def get_volume_aesa():
    global volume
    
    volume = float(get_volume("Pessoa"))
    


app = Flask(__name__)
setup(app)

@app.route("/get_notifications")
def get_notifications():
    response = make_response(json.dumps(notifications))
    response.headers['Access-Control-Allow-Origin'] = "*"
    
    return response

@app.route("/get_notifications_vazamentos")
def get_notifications_vazamentos():
    response = make_response(json.dumps(vazamentos))
    response.headers['Access-Control-Allow-Origin'] = "*"
    
    return response

@app.route("/get_volume_boqueirao")
def get_volume_boqueirao():
    response = make_response(json.dumps(volume))
    response.headers['Access-Control-Allow-Origin'] = "*"
    
    return response
