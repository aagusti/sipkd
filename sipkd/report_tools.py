import os
import sys
import ntpath
import csv
import io
from random import (
    randrange,
    choice,
    )
from datetime import datetime
from string import ascii_lowercase
from z3c.rml import rml2pdf

#rpt_path = "/home/aagusti/webr/webr/reports/"
#rpt_path = os.getcwd() 
from pyramid.path import AssetResolver
#rpt_path = AssetResolver().resolve("").abspath()
rpt_path = ""

def waktu():
    return datetime.now().strftime('%d-%m-%Y %H:%M')

def open_rml_row(row_tpl_filename):
    f = open(rpt_path+row_tpl_filename)
    row_rml = f.read()
    f.close()
    return row_rml

def open_rml_pdf(tpl_filename, **kwargs):
    pdf_filename = tpl_filename+'.pdf'
    
    f = open(rpt_path+tpl_filename)
    rml = f.read()
    f.close()
    params = {}
    
    for key, value in kwargs.iteritems():
        #if key == "logo":
        #    value = rpt_path+"/pajak/static/img/logo.png"
        params[key] = value

    rml = rml.format(waktu=waktu(), **kwargs)
    pdf = rml2pdf.parseString(rml)
    return pdf, pdf_filename
    
def pdf_response(request, pdf, filename):
    response=request.response
    response.content_type="application/pdf"
    response.content_disposition='filename='+filename 
    response.write(pdf.read())
    return response

def csv_rows(query):
    row = query.first()
    if not row:
        return 
        
    header = row.keys()
    rows = []
    for item in query.all():
        rows.append(list(item))
    return dict(header = header,
                rows = rows)
    
def csv_response(request, value, filename):
    if not value:
        return
    response = request.response
    response.content_type = 'text/csv'
    #response.content_disposition = 'attachment;filename=' + filename
    response.content_disposition = 'filename=' + filename
    
    fout = io.BytesIO() #StringIO()
    fcsv = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    fcsv.writerow(value.get('header', []))
    fcsv.writerows(value.get('rows', []))
    #return fout.getvalue()    
    response.write(fout.getvalue())
    return response
      