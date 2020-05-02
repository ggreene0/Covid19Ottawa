#!/usr/bin/env python3

"""
See oph.ipynb for reverse engineering/prototyping

- OPH page => PDF link
- PDF link => PDF file
- PDF file => text
- text => Table
- Table => CSV

Returns:
 - 0 if new PDF found (CSV updated)
 - 1 otherwise
"""

import requests as rq
from html.parser import HTMLParser
from PyPDF4 import PdfFileReader as PDFR
import os
import sys
import csv

"""
CONSTANTS
"""
OPH_url = 'https://www.ottawapublichealth.ca/en/reports-research-and-statistics/la-maladie-coronavirus-covid-19.aspx'
CSV_OUTPUT = 'timeseries/ottawa_cases.csv'

"""
CLASSES
"""

class PdfUrlParser(HTMLParser):
    """
    See https://docs.python.org/3/library/html.parser.html
    
    Just trying to populate self.pdf_url 
    by travesing the html tags
    
    Assumed the first pdf link we find 
    is the one we want
    """
    def __init__(self):
        super().__init__()
        self.pdf_url = None
    
    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            if self.pdf_url == None \
               and 'href' in attr[0] \
               and 'pdf' in attr[1]:
                self.pdf_url = '/'.join(OPH_url.split('/')[:3]) + attr[1]
                break
                

class DateNumTable(object):
    '''
    Need docstring here
    '''
    def __init__(self):
        self.dict = {}

    def is_date(self, line):
        # Date format is like 2/19/2020
        rc = False
        mdy = line.split('/')
        if len(mdy) == 3 \
           and all( [n.isnumeric() for n in mdy] ):
           rc = True
        return rc

    def cell_to_col_dict(self, slice, col_name, col_idx):
        for i in range(len(slice)):
            if self.is_date(slice[i]) \
               and slice[i+col_idx].isnumeric():
                if slice[i] not in self.dict:
                    self.dict[slice[i]] = { col_name: slice[i+col_idx] }
                else:
                    self.dict[slice[i]].update({ col_name: slice[i+col_idx] })
    

def main():
    '''
    - Get page
    - Find PDF link
    '''

    req = rq.get(OPH_url)
    parser = PdfUrlParser()
    parser.feed(req.text)

    PDF_url = parser.pdf_url

    '''
    Fetch PDF

    Looks like we need to save to get a 
    file pointer for the PDF Reader
    '''

    PDF_file = './pdf/' + os.path.basename(PDF_url)
    
    if not os.path.exists(PDF_file):

        pdfreq = rq.get(PDF_url)
        with open(PDF_file, 'wb') as f:
            f.write(pdfreq.content)

        print('Saved ' + PDF_file)

        # creating a pdf reader object
        fr = PDFR(PDF_file)

        text = ''
        for pgn in range(fr.numPages):
            pg = fr.getPage(pgn) 
            text = text + pg.extractText()

        '''
        Strip all newlines
        (random from one PDF to another)
        '''
        text = text.replace('\n', '')

        '''
        Find all instances of...
        "Data Table for Figure" case-insensitive (typo in the doc)
        
        Major rewrite of Data Tables for Figures 1 and 2 
        means pulling columns from two different Data Tables
        '''
        data_table_idxs = [i for i in range(len(text)) if text.upper().startswith('Data Table for Figure'.upper(), i)] 

        start1 = data_table_idxs[0]
        start2 = data_table_idxs[1]
        end = data_table_idxs[2]

        '''
        Lists of non-whitespace tokens
        First contains "Total" column; Second "Daily"
        '''
        snippet1 = text[start1:start2].split()
        snippet2 = text[start2:end].split()
        
        '''
        This results in dnt.dict looking like...
        {'2/19/2020': {'Total': '0', 'Daily': '0'},
         '2/20/2020': {'Total': '0', 'Daily': '0'},
         ...
         '4/24/2020': {'Total': '1106', 'Daily': '26'},
         '4/25/2020': {'Total': '1110', 'Daily': '4'}}
        '''
        dnt = DateNumTable()
        dnt.cell_to_col_dict(snippet1, 'Total', 1)
        dnt.cell_to_col_dict(snippet2, 'Daily', 1)

        with open('timeseries/ottawa_cases.csv', 'w', newline='') as csvfile:
            fieldnames = ['Date', 'Total', 'Daily']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for k in dnt.dict.keys():
                v = dnt.dict[k]
                row_dict = {
                    'Date': k, 
                    'Total': v['Total'],
                    'Daily': v['Daily'],
                }
                writer.writerow(row_dict)

        sys.exit(0)
    
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()