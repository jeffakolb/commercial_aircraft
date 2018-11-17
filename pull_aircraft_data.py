import sys
import argparse
import json
import datetime
import collections
import requests
import logging

from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument('-c','--config-file',
        dest='config_file',
        default='config/airlines.txt'
        )
parser.add_argument('-d','--dump-results-to-stdout',
        dest='dump',
        action='store_true',
        default=False
        )
parser.add_argument('-o','--output-file',
        dest='output_file',
        default='data/aircraft_data_' + datetime.date.today().isoformat() + '.json'
        ) 
parser.add_argument('-v','--verbose',
        dest='verbose',
        action='store_true',
        default=False
        )
args = parser.parse_args()

logging.getLogger().setLevel(logging.INFO)
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG) 


data = {} 

for line in open(args.config_file):
    tup = line.split(',')
    icao_code = tup[1].strip().rstrip()
    airline = tup[2].strip().rstrip(" \n")
    url = tup[3].strip().rstrip(" \n")
    data[icao_code] = {}
    data[icao_code]['url'] = url
    data[icao_code]['airline'] = airline

header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'} 

def get_fleet_table(table):
    for table_child in table.children:  
        #if table_child.name == "caption":
        #    logging.debug(table_child)
        if table_child.name == "tbody":
            return get_fleet_table(table_child)

        # find a tr child of table, with the correct properties
        if table_child.name == 'tr':
            # get the th elements in tr
            cells = table_child.find_all('th')
            # ensure there are enough cells in th
            if len(cells) < 3:
                continue
            # ensure str repr for first 3 cells is not None
            aircraft_str = cells[0].contents[0]
            orders_str = cells[2].contents[0]
            if aircraft_str.string is None or orders_str.string is None:
                continue
            if aircraft_str.string.lower().strip('\n').strip() == "aircraft" and \
                orders_str.string.lower().strip('\n').strip() == "orders":
                return table
    return None
    
for airline, airline_data in data.items(): 
    logging.info("Doing {}".format(airline))

    page = requests.get(airline_data['url'],headers=header)
    soup = BeautifulSoup(page.text,'lxml')
    tables = soup("table") 

    aircraft_data = {}
    airline_data['aircraft_data'] = aircraft_data


    fleet_table = None
    for tn,table in enumerate(tables):
        fleet_table = get_fleet_table(table)
        if fleet_table is not None:
            break
    if fleet_table is None:
        logging.error("no fleet table found for: " + airline)
        sys.exit(1)

    # this records how many rows must be aggregated 
    # to represent a single aircraft type
    craft_rowspan_idx = 0 
    # and these manage rowspans within an aircraft type
    inservice_rowspan_idx = 0 
    orders_rowspan_idx = 0 
    
    aircraft_type = ""
    n_row = 0
    for row in fleet_table.find_all('tr'):
        logging.debug('\nrow #' + str(n_row))
        n_row += 1
        cells = row.find_all('td')
        
        ## account for rowspans
        prev_craft_rowspan_idx = craft_rowspan_idx
        prev_orders_rowspan_idx = orders_rowspan_idx
        prev_inservice_rowspan_idx = inservice_rowspan_idx

        # first check state for aircraft type
        if craft_rowspan_idx > 0:
            # this row is for the aircraft in the previous row
            craft_rowspan_idx -= 1
        else: 
            # this row is the first for a new aircraft type
            try:
                craft_rowspan_idx = int(cells[0]['rowspan']) - 1
            except KeyError: 
                craft_rowspan_idx = 0
            except IndexError:
                craft_rowspan_idx = 0
        
        if inservice_rowspan_idx > 0:
            inservice_rowspan_idx -= 1
        else:
            try:
                inservice_rowspan_idx = int(cells[1]['rowspan']) - 1
            except KeyError: 
                inservice_rowspan_idx = 0
            except IndexError:
                inservice_rowspan_idx = 0
        if orders_rowspan_idx > 0:
            orders_rowspan_idx -= 1
        else:
            try:
                orders_rowspan_idx = int(cells[2]['rowspan']) - 1
            except KeyError: 
                orders_rowspan_idx = 0
            except IndexError:
                orders_rowspan_idx = 0

        logging.debug("craft_rowspan_idx is {}".format(craft_rowspan_idx))
        logging.debug("prev_craft_rowspan_idx is {}".format(prev_craft_rowspan_idx))
        logging.debug("inservice_rowspan_idx is {}".format(inservice_rowspan_idx))
        logging.debug("prev_inservice_rowspan_idx is {}".format(prev_inservice_rowspan_idx))
        logging.debug("orders_rowspan_idx is {}".format(orders_rowspan_idx))
        logging.debug("prev_orders_rowspan_idx is {}".format(prev_orders_rowspan_idx))
        
        # check for title or other non-informative rows
        if len(cells) < 3: 
            logging.debug('short row')
            continue
        
        # check for summary rows
        try:
            if "total" in cells[0].string.lower():
                continue
        except AttributeError:
            pass
  
        # get aircraft type
        if prev_craft_rowspan_idx == 0: 
            aircraft_type = cells[0].get_text().split('\n')[0]  
            logging.debug(aircraft_type) 
            aircraft_data[aircraft_type] = collections.defaultdict(int)

        # get indicies at which to look for counts
        if prev_craft_rowspan_idx == 0:
            # all data for this type are on a single line
            idx_n_in_service = 1
            idx_n_orders = 2
        else:


            if inservice_rowspan_idx < prev_inservice_rowspan_idx:
                idx_n_in_service = None
            else:
                idx_n_in_service = 0

            if orders_rowspan_idx < prev_orders_rowspan_idx:
                idx_n_orders = None
            else:
                if idx_n_in_service is None:
                    idx_n_orders = 0
                else:
                    idx_n_orders = 1

        # get counts of things
        try:
            this_n_in_service = int(cells[idx_n_in_service].contents[0])
        except (ValueError,TypeError) as e:
            this_n_in_service = 0
        logging.debug('idx_n_in_service: ' + str(idx_n_in_service))
        logging.debug('this_n_in_service: ' + str(this_n_in_service))
        
        try:
            this_n_orders = int(cells[idx_n_orders].contents[0]) 
        except (ValueError,TypeError) as e:
            this_n_orders = 0
        logging.debug('idx_n_orders: ' + str(idx_n_orders))
        logging.debug('this_n_orders: ' + str(this_n_orders))


        aircraft_data[aircraft_type]["in service"] += this_n_in_service    
        aircraft_data[aircraft_type]["orders"] += this_n_orders 


if args.dump:
    sys.stdout.write(json.dumps(data))
else:
    json.dump(data,open(args.output_file,'w'))
    
