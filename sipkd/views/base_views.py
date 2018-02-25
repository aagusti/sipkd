import os
from datetime import datetime
from ..tools import dmy, dmy_to_date

class BaseView(object):
    def __init__(self, request):
        #self.context = context
        self.req = request
        self.ses = self.req.session
        self.params = self.req.params
        
        self.tahun = 'tahun' in self.ses and self.ses['tahun'] or datetime.now().strftime('%Y')
        self.tahun = 'tahun' in self.params and self.params['tahun'] or self.tahun
        self.ses['tahun'] = self.tahun
                    
        self.posted = 'posted' in self.ses and self.ses['posted'] or 0
        if 'posted' in self.params and self.params['posted']:
             self.posted = self.params['posted']=='true' and 1 or 0
        self.ses['posted'] = self.posted
        
        self.awal   = 'awal' in self.ses and self.ses['awal'] or dmy(datetime.now())
        awal   = 'awal' in self.params and self.params['awal'] or self.awal
        try:
            self.dt_awal  = dmy_to_date(awal)
            self.awal = awal
        except:
            self.dt_awal  = dmy_to_date(self.awal)
        self.ses['awal'] = self.awal
        self.ses['dt_awal'] = self.dt_awal
        
        self.akhir  = 'akhir' in self.ses and self.ses['akhir'] or dmy(datetime.now())
        akhir  = 'akhir' in self.params and self.params['akhir'] or self.akhir
        try:
            self.dt_akhir = dmy_to_date(akhir)
            self.akhir = akhir
        except:
            self.dt_akhir = dmy_to_date(self.akhir)
        self.ses['akhir'] = self.akhir
        self.ses['dt_akhir'] = self.dt_akhir
        
        self.project = "project" in self.ses and self.ses["project"] or ''
        if "project" in self.params: # and self.params["project"]:
            self.project = self.params["project"] or ''
        self.ses["project"] = self.project

        _here = os.path.dirname(__file__)
        path = os.path.join(os.path.dirname(_here), 'static')
        self.logo = path + "/img/logo.png"
        self.line = path + "/img/line.png"
            