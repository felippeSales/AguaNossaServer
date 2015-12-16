# -*- coding: utf-8 -*-
import urllib  
import cgi
import json  
  
def find_index(headers, header_name):
    for i in range(0, len(headers)):
        if headers[i] == header_name:
            return i
    return -1

def geocode(addr):
    url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=true" %   (urllib.quote(addr.replace(' ', '+')))
    data = urllib.urlopen(url).read()
    results = json.loads(data).get("results")

    if (len(results) == 0):
        return ""
    else:
        info = results[0].get("geometry").get("location")
        return str(info['lat']) + " / " + str(info['lng'])

def cep_to_address(cep):
    url = "http://cep.republicavirtual.com.br/web_cep.php?cep=" + cep + "&formato=query_string"
    data = unicode(urllib.urlopen(url).read(), 'utf8')

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
    
    return result_dict

def build_complete_address(notification):
    complete_address = ''
   
    if (notification['address'] != ''):
        complete_address += notification['address'] + ','
    
    if (notification['number'] != ''):
        complete_address += notification['number'] + ','
    
    if (notification['number_for_cep'] != ''):
        complete_address += notification['number_for_cep'] + ','
    
    if (notification['district'] != ''):
        complete_address += notification['district'] + ','
        
    if (notification['state'] != ''):
        complete_address += notification['state'] + ','
        
    if (notification['city'] != ''):
        complete_address += notification['city']
   
    return complete_address.encode('utf-8')
   