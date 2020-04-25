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
                

class OPHTable(object):
    """
    Simple object to construct CSV rows 
    from text parsed from OPH PDF
    """
    def __init__(self):
        self.row = ['Date,Total,Daily']
        
    def add_row(self, date, total, daily):
        row = '%s,%s,%s' % (date, total, daily)
        self.row.append(row)
        
    def is_date(self, line):
        # Date format is like 2/19/2020
        rc = False
        mdy = line.split('/')
        if len(mdy) == 3 \
           and all( [n.isnumeric() for n in mdy] ):
           rc = True
        return rc
        
    def process(self, slice):
        for i in range(len(slice)):
            if i + 2 < len(slice) \
               and self.is_date(slice[i]) \
               and slice[i+1].isnumeric() \
               and slice[i+2].isnumeric():
                self.add_row(slice[i], slice[i+1], slice[i+2])

    def to_csv(self, filename):
        with open(filename, 'w')as csv:
            for row in self.row:
                csv.write(row + '\n')

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

        lines = text.split('\n')

        start = lines.index('Data Table for Figures 1 and 2')
        end = lines.index('Data Table for Figure 3')

        '''
        Need to get around some ugliness where the 
        PDF reader ends up with dates split across lines
        '''
        snippet = ''.join(lines[start:end]).split()

        table = OPHTable()
        table.process(snippet)
        table.to_csv(CSV_OUTPUT)

        sys.exit(0)
    
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()