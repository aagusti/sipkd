import os
import uuid
#from ..tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..models import (
    DBSession,
    Group
    )
    
from ..views.common import ColumnDT, DataTables    

    

SESS_ADD_FAILED = 'Tambah group gagal'
SESS_EDIT_FAILED = 'Edit group gagal'


                
class AddSchema(colander.Schema):
    group_name = colander.SchemaNode(
                    colander.String(),
                    oid = "group_name",
                    title = "Group",)
                    
    description = colander.SchemaNode(
                    colander.String(),
                    oid = "description",
                    title = "Deskripsi",)

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
########                    
# List #
########    
@view_config(route_name='group', renderer='templates/group/list.pt',
             permission='read')
def view_list(request):
    return dict(a={})
    
##########                    
# Action #
##########    
@view_config(route_name='group-act', renderer='json',
             permission='read')
def gaji_group_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT(Group.id, mData="id"))
        columns.append(ColumnDT(Group.group_name, mData="name"))
        columns.append(ColumnDT(Group.description, mData="desc"))
        columns.append(ColumnDT(Group.member_count, mData="member"))
        
        query = DBSession.query().select_from(Group)
        rowTable = DataTables(req.GET, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='headofnama':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Group.id, Group.group_name
                       ).filter(Group.group_name.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            r.append(d)
        return r                  
    
#######    
# Add #
#######
def form_validator(form, value):
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Group).filter_by(id=uid)
        group = q.first()
    else:
        group = None
            
def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
      schema.deserialize(row)
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = Group()
        #row.created = datetime.now()
        #row.create_uid = user.id
    row.from_dict(values)
    #row.updated = datetime.now()
    #row.update_uid = user.id
    #row.disabled = 'disabled' in values and values['disabled'] and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Group sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('group'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='group-add', renderer='templates/group/add.pt',
             permission='add')
def view_group_add(request):
    req = request
    ses = request.session
    form = get_form(request, AddSchema)
    if req.POST:
        if 'simpan' in req.POST:
            controls = req.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #req.session[SESS_ADD_FAILED] = e.render()    
                return dict(form=form)				
                return HTTPFound(location=req.route_url('group-add'))
            save_request(request, dict(controls))
        return route_list(request)
    elif SESS_ADD_FAILED in req.session:
        return session_failed(request,SESS_ADD_FAILED)
    #return dict(form=form.render())
    return dict(form=form)

    
########
# Edit #
########
def query_id(request):
    return DBSession.query(Group).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Group ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list()

@view_config(route_name='group-edit', renderer='templates/group/add.pt',
             permission='group-edit')
def view_edit(request):
    #request = request
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('group-edit',
                                  id=row.id))
            save_request(request, dict(controls), row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request,SESS_EDIT_FAILED)
    values = row.to_dict()
    #return dict(form=form.render(appstruct=values))
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='group-delete', renderer='templates/group/delete.pt',
             permission='delete')
def view_delete(request):
    request = request
    q = Group.query_id(request.matchdict['id'])
    row = q.first()
    
    if not row:
        return request.id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Group ID %d %s sudah dihapus.' % (row.id, row.description)
            try:
              q.delete()
              DBSession.flush()
            except:
              msg = 'Group ID %d %s tidak dapat dihapus.' % (row.id, row.description)
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# RPT    #
##########    
from ..report_tools import open_rml_row, open_rml_pdf, pdf_response, csv_response

@view_config(route_name='group-rpt', permission='group-rpt')
def view_rpt(request):
    def query_reg():
        return DBSession.query(Group.group_name, Group.description, 
                    Group.member_count).order_by(Group.group_name)
    params   = request.params
    url_dict = request.matchdict
    if url_dict['rpt']=='pdf' :
        query = query_reg()
        _here = os.path.dirname(__file__)
        path = os.path.join(os.path.dirname(_here), 'static')
        logo = path + "/img/logo.png"
        line = path + "/img/line.png"
        
        path = os.path.join(os.path.dirname(_here), 'reports')
        rml_row = open_rml_row(path+'/group.row.rml')
        
        rows=[]
        for r in query.all():
            s = rml_row.format(group_name=r.group_name, 
                               description=r.description, 
                               member_count=r.member_count
                               )
            rows.append(s)
        
        pdf, filename = open_rml_pdf(path+'/group.rml', rows=rows, 
                            company=request.company,
                            departement = request.departement,
                            logo = logo,
                            line = line,
                            address = request.address)
        return pdf_response(request, pdf, filename)
        
    elif url_dict['rpt']=='csv' :
        query = query_reg() 
        row = query.first()
        header = row.keys()
        rows = []
        for item in query.all():
            rows.append(list(item))

        filename = 'user.csv'
        value = {
                  'header': header,
                  'rows'  : rows,
                } 
        return csv_response(request, value, filename)
