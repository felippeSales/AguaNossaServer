# -*- coding: utf-8 -*-
from flask import Flask
from util import find_index, geocode, cep_to_address, build_complete_address
import json
import gspread
from threading import Thread
import time

notifications = []
lat_lng_array = []
worksheet = None

ADDRESS_HEADER = 'Nome da rua:'.decode('utf-8')
CEP_HEADER = 'CEP:'.decode('utf-8')
NUMBER_HEADER = 'Número:'.decode('utf-8')
NUMBER_FOR_CEP_HEADER = 'Número do domicílio:'.decode('utf-8') # Número do domicílio - quando tem CEP
DISTRICT_HEADER = 'Bairro:'.decode('utf-8')
CITY_HEADER = 'Cidade:'.decode('utf-8')
STATE_HEADER = 'Estado:'.decode('utf-8')
LAT_LNG_HEADER = 'Latitude / Longitude'.decode('utf-8')

UPDATE_TIME = 2 # seconds

def setup():
    global ADDRESS_INDEX, CEP_INDEX, NUMBER_INDEX, NUMBER_FOR_CEP_INDEX, DISTRICT_INDEX, STATE_INDEX, CITY_INDEX, LAT_LNG_INDEX
    
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
    
    t = Thread(target=notification_thread)
    t.start()
    return

def read_worksheet():
   gc = gspread.login('aguanossa.cg@gmail.com', '4gu4n6ss4-cg')
   sht1 = gc.open_by_key('1Y4RXKYvdFKCtf6RMyQCjSS7iN-5AfyedfTbJa_vDO5g')
   worksheet = sht1.get_worksheet(0)
   return worksheet

def notification_thread():
    while True:
        try:
            retrieve_notifications()
        except Exception as e:
            print('Error %s' % e)
        finally:
            time.sleep(UPDATE_TIME)

def retrieve_notifications():
    global notifications, lat_lng_array, worksheet
    
    worksheet = read_worksheet()
    rows = worksheet.get_all_values()
    current_index  = len(notifications) + 1
    
    for i in range(current_index, len(rows)):
        notification = process_worksheet_row(rows[i], i+1)
        notifications.append(notification)
        lat_lng_array.append(notification['lat_lng'])

def process_worksheet_row(row, worksheet_row_index):
    notification = dict(cep = row[CEP_INDEX], address = row[ADDRESS_INDEX], number = row[NUMBER_INDEX], number_for_cep= row[NUMBER_FOR_CEP_INDEX], district = row[DISTRICT_INDEX], state = row[STATE_INDEX], city = row[CITY_INDEX], lat_lng = row[LAT_LNG_INDEX])
    
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
        print(build_complete_address(notification))
        address_geocode = geocode(build_complete_address(notification))
        notification['lat_lng'] = address_geocode
        update_cell(worksheet_row_index, LAT_LNG_INDEX+1, address_geocode)
        
    return notification

def update_cell(row, col, val):
   if worksheet == None:
       return
   worksheet.update_cell(row, col, val)

app = Flask(__name__)
setup()

@app.route("/get_notifications")
def get_notifications():
    return json.dumps(lat_lng_array)
