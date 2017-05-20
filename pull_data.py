import sys
import json

import requests
from bs4 import BeautifulSoup

data = {}
data['all nippon'] = {}
data['all nippon']['url'] = 'https://en.wikipedia.org/wiki/All_Nippon_Airways' 
data['delta'] = {}
data['delta']['url'] = 'https://en.wikipedia.org/wiki/Delta_Air_Lines_fleet'
data['american'] = {}
data['american']['url'] = 'https://en.wikipedia.org/wiki/American_Airlines_fleet'
data['united'] = {}
data['united']['url'] = 'https://en.wikipedia.org/wiki/United_Airlines' 
data['southwest'] = {}
data['southwest']['url'] = 'https://en.wikipedia.org/wiki/Southwest_Airlines'
data['air new zealand'] = {}
data['air new zealand']['url'] = 'https://en.wikipedia.org/wiki/Air_New_Zealand' 
data['alitalia'] = {}
data['alitalia']['url'] = 'https://en.wikipedia.org/wiki/Alitalia' 
data['british'] = {}
data['british']['url'] = 'https://en.wikipedia.org/wiki/British_Airways'
data['air france'] = {}
data['air france']['url'] = 'https://en.wikipedia.org/wiki/Air_France'
data['klm'] = {}
data['klm']['url'] = 'https://en.wikipedia.org/wiki/KLM' 
data['alaskan'] = {}
data['alaskan']['url'] = 'https://en.wikipedia.org/wiki/Alaska_Airlines'  
data['eva air'] = {}
data['eva air']['url'] = 'https://en.wikipedia.org/wiki/EVA_Air'
data['air canada'] = {}
data['air canada']['url'] = 'https://en.wikipedia.org/wiki/Air_Canada'
data['lufthansa'] = {}
data['lufthansa']['url'] = 'https://en.wikipedia.org/wiki/Lufthansa'
data['qantas'] = {}
data['qantas']['url'] = 'https://en.wikipedia.org/wiki/Qantas'
data['emirates'] = {}
data['emirates']['url'] = 'https://en.wikipedia.org/wiki/Emirates_fleet'
data['hawaiian'] = {}
data['hawaiian']['url'] = 'https://en.wikipedia.org/wiki/Hawaiian_Airlines'
data['etihad'] = {}
data['etihad']['url'] = 'https://en.wikipedia.org/wiki/Etihad_Airways#Fleet' 
data['qatar'] = {}
data['qatar']['url'] = 'https://en.wikipedia.org/wiki/Qatar_Airways#Current_fleet'  
data['virgin atlantic'] = {}
data['virgin atlantic']['url'] = 'https://en.wikipedia.org/wiki/Virgin_Atlantic#Fleet'   
data['japan airlines'] = {}
data['japan airlines']['url'] = 'https://en.wikipedia.org/wiki/Japan_Airlines#Fleet'

#header = {'User-Agent': 'Mozilla/5.0'}
header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'} 

for airline, airline_data in data.items(): 
    print("Doing {}".format(airline))

    page = requests.get(airline_data['url'],headers=header)
    soup = BeautifulSoup(page.text,'lxml')
    tables = soup("table") 

    aircraft_data = {}
    airline_data['aircraft_data'] = aircraft_data
    for tn,table in enumerate(tables):
        
        is_fleet_table = False
        for table_child in table.children: 
            # find a tr child of table, with the correct properties
            if table_child.name == 'tr':
                # get the th elements in tr
                cells = table_child.find_all('th')
                # ensure there are enough cells in th
                if len(cells) < 3:
                    continue
                # ensure str repr for first 3 cells is not None
                if cells[0].string is None or cells[2].string is None:
                    continue
                if cells[0].string.lower() == "aircraft" and \
                    cells[2].string.lower() == "orders":
                    #cells[1].string.lower() == "in service" and \
                    is_fleet_table = True
        if not is_fleet_table:
            continue
       
        n_rowspan = 0
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            # account for rowspans 
            if n_rowspan > 0:
                n_rowspan -= 1
                continue
            try:
                n_rowspan = int(cells[0]['rowspan']) - 1
            except KeyError: 
                pass 
            except IndexError:
                continue

            try:
                # check for summary rows
                if "total" in cells[0].string.lower():
                    continue
            except AttributeError:
                pass
            
            aircraft_type = cells[0].get_text().split('\n')[0]
            
            # tables use "-" to indicate zero count
            try:
                n_in_service = int(cells[1].contents[0])
            except ValueError:
                n_in_service = 0
            #except TypeError:
            #    n_in_service = -1
            # tables use "-" to indicate zero count
            try:
                n_orders = int(cells[2].contents[0]) 
            except ValueError:
                n_orders = 0
            except TypeError:
                # this gets thrown when there's a row span across multiple aircraft
                n_orders = -1

            aircraft_data[aircraft_type] = { "in service" : n_in_service, "orders" : n_orders}   
        
        # after processing correct table, break out of table loop
        break


                
json.dump(data,open('aircraft_data.json','w'))
    
