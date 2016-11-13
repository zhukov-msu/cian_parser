# -*- coding: utf-8 -*-
from cian_parser import Parser, FlatStats
import csv

if __name__ == '__main__':
    p = Parser()
    flats = p.walk(2)  # можно не указывать, тогда будут все страницы
    fs = FlatStats(flats)
    fs.get_stats()

    with open('flats.csv', 'w', newline="\n", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=flats[0].keys(), lineterminator='\n')
        writer.writeheader()
        writer.writerows(flats)
    # flats = []
    # with open('flats1.csv', 'r', newline="\n", encoding="utf-8") as csvfile:
    #     reader = csv.DictReader(csvfile)
    #     for row in reader:
    #         flats += [row]
