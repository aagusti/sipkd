from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    )
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
import transaction
import colander
from deform import (
    Form,
    ValidationFailure,
    widget,
    )
from ..tools import create_now
from ..models import (
    DBSession,
    User,
    )


########
# Home #
########
@view_config(route_name='home', renderer='templates/home.pt', permission='view')
def view_home(request):
    return dict(project='sipkd')


#########
# Login #
#########
class Login(colander.Schema):
    username = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(colander.String(),
                    widget=widget.PasswordWidget())


# http://deformdemo.repoze.org/interfield/
def login_validator(form, value):
    user = form.user
    if not user:
        raise colander.Invalid(form, 'Login failed')
    if not user.user_password:
        raise colander.Invalid(form, 'Login failed')        
    if not user.check_password(value['password']):
        raise colander.Invalid(form, 'Login failed')

def get_login_headers(request, user):
    headers = remember(request, user.email)
    user.last_login_date = create_now()
    DBSession.add(user)
    DBSession.flush()
    transaction.commit()
    return headers

@view_config(context=HTTPForbidden, renderer='templates/login.pt')
@view_config(route_name='login', renderer='templates/login.pt')
def view_login(request):
    if authenticated_userid(request):
        return HTTPFound(location=request.route_url('home'))
    schema = Login(validator=login_validator)
    form = Form(schema, buttons=('login',))
    if 'login' in request.POST: 
        controls = request.POST.items()
        identity = request.POST.get('username')
        user = schema.user = User.get_by_identity(identity)
        try:
            c = form.validate(controls)
        except ValidationFailure, e:
            request.session['login failed'] = e.render()
            return HTTPFound(location=request.route_url('login'))
        #####################################################
        request.session['tahun'] = datetime.now().year
        request.session['tanggal'] = datetime.today()
        request.session['tanggal_to'] = datetime.today()
        request.session['unit_id'] = 0
        request.session['unit_kd'] = ""
        request.session['unit_nm'] = ""
        request.session['rekening_kd'] = ""
        request.session['rekening_nm'] = ""
        request.session['rekening_id'] = ""
        headers = get_login_headers(request, user)
        
        
        return HTTPFound(location=request.route_url('home'),
                          headers=headers)
    elif 'login failed' in request.session:
        r = dict(form=request.session['login failed'])
        del request.session['login failed']
        return r
    return dict(form=form.render())

@view_config(route_name='logout')
def view_logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('home'),
                      headers = headers)    


###################
# Change password #
###################
class Password(colander.Schema):
    old_password = colander.SchemaNode(colander.String(),
                                       widget=widget.PasswordWidget())
    new_password = colander.SchemaNode(colander.String(),
                                       widget=widget.PasswordWidget())
    retype_password = colander.SchemaNode(colander.String(),
                                          widget=widget.PasswordWidget())

                                          
def password_validator(form, value):
    if not form.request.user.check_password(value['old_password']):
        raise colander.Invalid(form, 'Invalid old password.')
    if value['new_password'] != value['retype_password']:
        raise colander.Invalid(form, 'Retype mismatch.')
                                          

@view_config(route_name='password', renderer='templates/password.pt',
             permission='view')
def view_password(request):
    schema = Password(validator=password_validator)
    form = Form(schema, buttons=('save','cancel'))
    if request.POST:
        if 'save' in request.POST:
            schema.request = request
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session['invalid password'] = e.render()
                return HTTPFound(location=request.route_url('password'))
            user = request.user
            user.password = c['new_password']
            DBSession.add(user)
            DBSession.flush()
            transaction.commit()
            request.session.flash('Your password has been changed.')
        return HTTPFound(location=request.route_url('home'))
    elif 'invalid password' in request.session:
        r = dict(form=request.session['invalid password'])
        del request.session['invalid password']
        return r
    return dict(form=form.render())
