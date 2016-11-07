from datetime import datetime
class base_view(object):
    def __init__(self, request):
        self.req = request
        self.ses = self.req.session
        if 'tahun' not in self.ses or self.ses['tahun']==None:
            self.ses['tahun'] = datetime.now().year
        if 'tanggal' not in self.ses or self.ses['tanggal']==None:
            self.ses['tanggal'] = datetime.now().strftime('%Y-%m-%d')
        if 'tanggal_to' not in self.ses or self.ses['tanggal_to']==None:
            self.ses['tanggal_to'] = self.ses['tanggal']
        if 'posted' not in self.ses:
            self.ses['posted'] = 0
    
        
            