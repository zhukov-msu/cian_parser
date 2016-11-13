import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import time
import multiprocessing
from html_helpers import *
from math import sqrt


class Parser:

    ads_on_page = 28

    def __init__(self):
        self.districts = {
            'CAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=4&engine_version=2&offer_type=flat&p={}&'
                   'room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'SAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=5&engine_version=2&offer_type=flat&p={}&'
                   'room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'SVAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=6&engine_version=2&offer_type=flat&p={}&'
                    'room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'VAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=7&engine_version=2&offer_type=flat&p={}&'
                   'room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'UVAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=8&engine_version=2&offer_type=flat&p={}&'
                    'room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'UAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=9&engine_version=2&'
                   'offer_type=flat&p={}&room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'UZAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=10&engine_version=2&offer_type=flat'
                    '&p={}&room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'ZAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=11&engine_version=2&offer_type=flat&p={}'
                   '&room1=1&room2=1&room3=1&room4=1&room5=1&room6=1',
            'SZAO': 'http://www.cian.ru/cat.php?deal_type=sale&district%5B0%5D=1&engine_version=2&offer_type=flat&p={}'
                    '&room1=1&room2=1&room3=1&room4=1&room5=1&room6=1'
        }

    def walk(self, pages=None):
        flats = []
        for district, url in self.districts.items():
            print("parsing: {}".format(district))
            first_page = BeautifulSoup(requests.get(url.format('1')).content, 'lxml')
            count_flats = first_page.findAll('div', attrs={"class": "serp-above__count"})
            count_flats = re.findall('[0-9]+', str(count_flats))
            if len(count_flats) == 1:
                count_flats = int(count_flats[0])
            else:
                raise Exception("page count not found :(")
            count_pages = count_flats // self.ads_on_page + 1
            for page in range(1, pages if pages else count_pages):
                page_url = url.format(page)
                search_page = requests.get(page_url)
                search_page = search_page.content
                search_page = BeautifulSoup(search_page, 'lxml')
                flat_urls = search_page.findAll('div', attrs={
                    'ng-class': "{'serp-item_removed': offer.remove.state, 'serp-item_popup-opened': isPopupOpen}"})
                flat_urls = re.split('http://www.cian.ru/sale/flat/|/" ng-class="', str(flat_urls))
                flats += [{"district": district, "url": link} for link in flat_urls if link.isdigit()]
        return flats


class FlatStats:

    center_coord = (55.751981, 37.617466)
    def __init__(self, flats):
        self.flats = flats
        self.flat_stats = {}

    @staticmethod
    def get_flat_page(link):
        flat_url = 'http://www.cian.ru/sale/flat/' + str(link) + '/'
        flat_page = requests.get(flat_url)
        flat_page = flat_page.content
        flat_page = BeautifulSoup(flat_page, 'lxml')
        return flat_page

    @staticmethod
    def coord_dist(c1, c2):
        return sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)


    def get_stats(self):
        for i, flat in enumerate(self.flats):
            page = self.get_flat_page(flat['url'])
            if "Ошибка 404" in page:
                continue
            # try:
            coords = self.get_coords(page)
            self.flats[i]['price'] = self.get_price(page)
            self.flats[i]['coords'] = coords
            self.flats[i]['rooms'] = self.get_rooms(page)
            self.flats[i].update(self.get_table_data(page))
            self.flats[i]['Metrdist'], self.flats[i]['Walk'] = self.get_metro(page)
            self.flats[i]['Dist'] = self.coord_dist(self.center_coord, coords)

            # except Exception as e:
            #     print(e)
            #     print("ERROR in: {}".format(flat['url']))
            #     continue


    @staticmethod
    def get_price(flat_page):
        price = flat_page.find('div', attrs={'class': 'object_descr_price'})
        price = re.split('<div>|руб|\W', str(price))
        price = "".join([i for i in price if i.isdigit()][-3:])
        if price:
            return int(price)
        else:
            print(flat_page)

    @staticmethod
    def get_coords(flat_page):
        coords = flat_page.find('div', attrs={'class': 'map_info_button_extend'}).contents[1]
        coords = re.split('&amp|center=|%2C', str(coords))
        coords_list = []
        for item in coords:
            if item[0].isdigit():
                coords_list.append(item)
        lat = float(coords_list[0])
        lon = float(coords_list[1])
        return lat, lon

    @staticmethod
    def get_metro(flat_page):
        time = 0
        walk = 0
        metro = flat_page.find('span', attrs={"class": "object_item_metro_comment"})
        if metro:
            metro = html_stripper(metro)
            spl = re.split('-|\n', metro)
            for i, word in enumerate(spl):
                if 'мин' in word:
                    if spl[i-1].strip().isdigit():
                        time = int(spl[i-1].strip())
                if 'пешком' in word:
                    walk = 1
                if time > 0 and walk > 0:
                    break
            return time, walk
        else:
            return None, None

    @staticmethod
    def get_rooms(flat_page):
        rooms = flat_page.find('div', attrs={'class': 'object_descr_title'})
        rooms = html_stripper(rooms)
        room_number = ''
        for i in re.split('-|\n', rooms):
            if 'комн' in i:
                break
            else:
                room_number += i
        room_number = "".join(room_number.split())
        if room_number:
            return int(room_number)
        else:
            return 0

    def get_table_data(self, flat_page):
        data = {}
        table = flat_page.find('table', attrs={'class': 'object_descr_props'})
        table = html_stripper(table)
        text = table.split()
        try:
            total_idx = 0
            while text[total_idx] != 'площадь:':
                total_idx = text.index('Общая')
                del text[total_idx]
            if text[total_idx+1].isdigit():
                data['totsp'] = int(text[total_idx+1])
            else:
                data['totsp'] = 0
        except:
            data['totsp'] = 0

        try:
            live_idx = text.index('Жилая')
            if text[live_idx+1] == 'площадь:' and text[live_idx+2].isdigit():
                data['livesp'] = int(text[live_idx+2])
            else:
                data['livesp'] = 0
        except:
            data['livesp'] = 0
        try:
            kitch_idx = text.index('кухни:')
            if text[kitch_idx+1].isdigit():
                data['kitsp'] = int(text[kitch_idx + 1])
            else:
                data['kitsp'] = 0
        except:
            data['kitsp'] = 0
        return data



