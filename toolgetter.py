#toolgetter.py

# NOTES:
# 1) I've started trying to read speed/feed data out of the PDF but it's really hard, so thats incomplete
# 2) Weirdly enough, Harvey doesn't put tool diameters on their tool pages, so I still need to figure out how the heck I am going to deal with that issue.

import requests
from lxml import html
from PyPDF2 import PdfFileReader
import io

unit = 'inches'

# P/N Prefixes for each vendor
vendorCodes = {
    'HarveyTool' : 'HTC'
}

# This is just here for reference
fusionModel = {
    'BMC' : 'material',
    'GRADE' : 'not sure',
    'description' : 'tool name',
    'geometry' : {
        'CSP': 'no clue',
        'DC': 'diameter',
        'HAND': 'true:false, RH = True',
        'LB': 'length below holder',
        'LCF': 'length of cut',
        'NOF': 'no of flutes',
        "NT": 'shoulder length',
        "OAL": 'overall length',
        "RE": 'no clue',
        "SFDM": 'shaft diam',
        "TA": 'no clue',
        "TP": 'no clue',
        "shoulder-length": 'shoulder length',
        "thread-profile-angle": 'thread profile angle',
        "tip-diameter": 'tip diam',
        "tip-length": 'tip length',
        "tip-offset": 'tip offset'
    },
    'product-id': 'part no',
    'product-link': 'url',
    'type': 'tool type, as per fusion options',
    'unit': 'unit, inches:mm',
    'vendor': 'vendor, for use with Chatter Setups enter URL here since the post can\'t access native url parameter'
}

def getToolInfo(pn, vendor):
    if vendor == 'HarveyTool':

        toolDiam = .1 # Hard coded this for testing bc I still haven't figured out how to scrape diam form Harvey tool

        minShaftDiam = .125

        # Where to grab the tool from
        basePath = 'https://www.harveytool.com/products/tool-details-'
        targetPath = basePath + str(pn)

        # Get the web page
        r = requests.get(targetPath)

        # Exit if there's a problem
        if r.status_code != 200:
            exit('An error has occurred')

        # Get DOM
        tree = html.fromstring(r.content)

        # Get Desc / Value and combine into dict
        dimNames = tree.xpath('//ul[@class="dimension-list"]/li/span[@class="dimension-text"]/text()')
        dimValues = tree.xpath('//ul[@class="dimension-list"]/li/span[@class="dimension-value"]/text()')
        dims = {}
        for i, name in enumerate(dimNames):
            x = dimValues[i]
            if '"' in x:
                x = x[:x.index('"')]
            dims[name.rstrip(':')] = x

        # Get some other stuff
        tName = tree.xpath('//h1[@class="titlePDP"]/text()')
        tMaterial = 'carbide' # Not supported by Harvey site, they only sell carbide
        tGrade = 'Mill Generic' # Not supported by Harvey site, not sure what this even is tbh
        tPID = vendorCodes[vendor] + ' ' + str(pn)

        # Get tool type, this is not complete
        if 'Profile' in dims:
            if dims['Profile'] == 'Square':
                tType = 'flat end mill'
            else:
                tType = ''

        
        # Get speeds and feeds (this part is supppppper in-progress, reading a pdf is hard)
        sfUrl = tree.xpath('//a[@aria-label="Download Speeds & Feeds PDF"]/@href')[0]
        r = requests.get(sfUrl)
        f = io.BytesIO(r.content)
        reader = PdfFileReader(f)
        contents = reader.getPage(0).extractText().split('\n')

        # Get the tool speed/feed diameters from the table
        f = str(contents[0]).rstrip('RadialAxial')
        d = "."
        diams =  [d+e for e in f.split(d) if e][1:]

        retDict = {
            'BMC' : tMaterial,
            'GRADE' : tGrade,
            'description' : tName,
            'geometry' : {
                'CSP': '', # no clue what this is
                'DC': toolDiam,
                'HAND': True, # Clockwise rotation
                'LB': dims['Length of Cut'], # default to LOC, user can change this later
                'LCF': dims['Length of Cut'],
                'NOF': dims['Flutes'],
                "NT": dims['Length of Cut'], # again, default to LOC
                "OAL": float(dims['Length of Cut']) * 3, # 3x LOC ¯\_(ツ)_/¯
                "RE": '', # no clue what this is
                "SFDM": minShaftDiam if toolDiam < minShaftDiam else toolDiam, # we can safely assume that if the tool is under .125, its a .125 shaft
                "TA": '', # no clue what this is
                "TP": '', # no clue what this is
                "shoulder-length": dims['Length of Cut'],
                "thread-profile-angle": '',
                "tip-diameter": toolDiam,
                "tip-length": 0,
                "tip-offset": 0
            },
            'product-id': tPID,
            'product-link': targetPath,
            'type': tType,
            'unit': unit,
            'vendor': targetPath
        }
        return retDict
    else:
        exit('Unsupported Tool Vendor')

print('Welcome to Tool Getter!')
pn = '942210'
vendor = 'HarveyTool'
out = getToolInfo(pn, vendor)
print(out)
