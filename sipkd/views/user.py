import os
from email.utils import parseaddr
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
    User,
    )
from ..views.common import ColumnDT, DataTables    


from ..tools import _DTstatus
SESS_ADD_FAILED = 'user add failed'
SESS_EDIT_FAILED = 'user edit failed'

########                    
# List #
########    
@view_config(route_name='user', renderer='templates/user/list.pt',
             permission='user')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(project='Pajak Reklame')
    
#######    
# Add #
#######
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')

def form_validator(form, value):
    def err_email():
        raise colander.Invalid(form,
            'Email %s already used by user ID %d' % (
                value['email'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'User name %s already used by ID %d' % (
                value['user_name'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(User).filter_by(id=uid)
        user = q.first()
    else:
        user = None
        
    q = DBSession.query(User).filter_by(email=value['email'])
    found = q.first()
    if user:
        if found and found.id != user.id:
            err_email()
    elif found:
        err_email()
    if 'user_name' in value: # optional
        found = User.get_by_name(value['user_name'])
        if user:
            if found and found.id != user.id:
                err_name()
        elif found:
            err_name()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )    

class AddSchema(colander.Schema):
    email = colander.SchemaNode(
                    colander.String(),
                    validator=email_validator,
                    oid = "email",
                    title = "E-mail",)
    user_name = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid = "user_name",
                    title = "Username",)
    password = colander.SchemaNode(
                    colander.String(),
                    widget=widget.PasswordWidget(),
                    missing=colander.drop,
                    oid = "password",
                    title = "Password",)
    status = colander.SchemaNode(
                    colander.String(),
                    widget=deferred_status)


class EditSchema(AddSchema):
    id = colander.SchemaNode(
            colander.Integer(),
            oid="id")
    #id = colander.SchemaNode(colander.String(),
    #        missing=colander.drop,
    #        widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = User()
    row.from_dict(values)
    if values['password']:
        row.password = values['password']
        #row.rpc_password = values['password']
        
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('User %s berhasil disimpan.' % row.email)
        
def route_list(request):
    return HTTPFound(location=request.route_url('user'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='user-add', renderer='templates/user/add.pt',
             permission='user-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #request.session[SESS_ADD_FAILED] = e.render()  
                return dict(form=form)
                return HTTPFound(location=request.route_url('user-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    #return dict(form=form.render())
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(User).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='user-edit', renderer='templates/user/edit.pt',
             permission='user-edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            if row.id==1 and request.user.id>1 :
                request.session.flash('User tidak mempunyai hak akses mengupdate data user admin', 'error')
                return route_list(request)
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('user-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    #return dict(form=form.render(appstruct=values))
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='user-delete', renderer='templates/user/delete.pt',
             permission='user-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    if row.id==1 and request.user.id>1 :
        request.session.flash('User tidak mempunyai hak akses menghapus data user admin', 'error')
        return route_list(request)

    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'User ID %d %s berhasil dihapus.' % (row.id, row.email)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

def array_of_rows(rows):
    r = []
    for k in rows:
        d={}
        d['id']          = k[0]
        d['value']       = k[1]
        r.append(d)
    return r        


##########                    
# Action #
##########    
@view_config(route_name='user-act', renderer='json',
             permission='user-act')
def user_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = [
        ColumnDT(User.id, mData='id'),
        ColumnDT(User.email, mData='email'),
        ColumnDT(User.user_name, mData='name'),
        ColumnDT(User.status, mData='status'), #, filter=_DTstatus
        ColumnDT(func.to_char(User.last_login_date, 'DD-MM-YYYY'), mData='last_login'),
        ColumnDT(func.to_char(User.registered_date, 'DD-MM-YYYY'), mData='registered'),
        ]
        query = DBSession.query().select_from(User)
        rowTable = DataTables(req.GET, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='hon':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(User.id, User.user_name
                       ).filter(
                            User.id>1,
                            User.user_name.ilike('%%%s%%' % term) 
                       ).all()
        return array_of_rows(rows)
        
    elif url_dict['act']=='homail':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(User.id, User.email
                       ).filter(User.id!='1',
                                User.id!='2',
                                User.email.ilike('%%%s%%' % term) 
                       ).all()
        return array_of_rows(rows)
        
##########
# RPT    #
##########    
from ..report_tools import open_rml_row, open_rml_pdf, pdf_response, csv_response

@view_config(route_name='user-rpt', permission='user-rpt')
def view_rpt(request):
    def query_reg():
        return DBSession.query(User.user_name, User.email, 
                    func.to_char(User.registered_date,"DD-MM-YYYY").label("registered_date")).order_by(User.user_name)
    params   = request.params
    url_dict = request.matchdict
    if url_dict['rpt']=='pdf' :
        query = query_reg()
        _here = os.path.dirname(__file__)
        path = os.path.join(os.path.dirname(_here), 'static')
        logo = path + "/img/logo.png"
        line = path + "/img/line.png"
        
        path = os.path.join(os.path.dirname(_here), 'reports')
        rml_row = open_rml_row(path+'/user.row.rml')
        
        rows=[]
        for r in query.all():
            s = rml_row.format(user_name=r.user_name, email=r.email, 
                               registered_date=r.registered_date)
            rows.append(s)
        
        pdf, filename = open_rml_pdf(path+'/user.rml', rows=rows, 
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
