import locale
try:
    from urllib.parse import (urlencode, quote, quote_plus,)
except:
    from urllib import (urlencode, quote, quote_plus,)
from types import (UnicodeType, StringType)
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.interfaces import IRoutesMapper
from pyramid.httpexceptions import (
    default_exceptionresponse_view,
    HTTPFound,
    )
from pyramid.renderers import JSON
import datetime, decimal, time
from sqlalchemy import engine_from_config
from .security import (
    group_finder,
    get_user,
    )
from .models import (
    DBSession,
    Base,
    init_model,
    Route
    )
from .tools import (
    DefaultTimeZone,
    money,
    should_int,
    thousand,
    as_timezone,
    split,
    get_settings,
    dmy,
    )

# http://stackoverflow.com/questions/9845669/pyramid-inverse-to-add-notfound-viewappend-slash-true
class RemoveSlashNotFoundViewFactory(object):
    def __init__(self, notfound_view=None):
        if notfound_view is None:
            notfound_view = default_exceptionresponse_view
        self.notfound_view = notfound_view

    def __call__(self, context, request):
        if not isinstance(context, Exception):
            # backwards compat for an append_notslash_view registered via
            # config.set_notfound_view instead of as a proper exception view
            context = getattr(request, 'exception', None) or context
        path = request.path
        registry = request.registry
        mapper = registry.queryUtility(IRoutesMapper)
        if mapper is not None and path.endswith('/'):
            noslash_path = path.rstrip('/')
            for route in mapper.get_routes():
                if route.match(noslash_path) is not None:
                    qs = request.query_string
                    if qs:
                        noslash_path += '?' + qs
                    return HTTPFound(location=noslash_path)
        return self.notfound_view(context, request)

# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def has_permission_(request, perm_names):
    if type(perm_names) in [str]:
        perm_names = [perm_names]
    for perm_name in perm_names:
        if request.has_permission(perm_name):
            return True

@subscriber(BeforeRender)
def add_global(event):
     event['has_permission'] = has_permission_
     event['urlencode'] = urlencode
     event['quote_plus'] = quote_plus
     event['quote'] = quote
     event['money'] = money
     event['should_int'] = should_int
     event['thousand'] = thousand
     event['as_timezone'] = as_timezone
     event['split'] = split
     event['allow_register'] = allow_register
     event['change_unit'] = change_unit

def allow_register(request):
    settings = get_settings()
    allow_register = 'allow_register' in settings and settings['allow_register']=='true' or False
    return allow_register

def change_unit(request):
    settings = get_settings()
    change_unit = 'change_unit' in settings and settings['change_unit']=='true' or False
    return change_unit

def get_title(request):
    route_name = request.matched_route.name
    return titles[route_name]

def get_company(request):
    settings = get_settings()
    company = 'company' in settings and settings['company'] or 'openSIPKD'
    return company.upper()

def get_departement(request):
    settings = get_settings()
    departement = 'departement' in settings and settings['departement'] or 'DEPARTEMEN INFORMATION TEKNOLOGI'
    return departement

def get_ibukota(request):
    settings = get_settings()
    ibukota = 'ibukota' in settings and settings['ibukota'] or 'BEKASI'
    return ibukota

def get_address(request):
    settings = get_settings()
    address_1 = 'address_1' in settings and settings['address_1'] or 'ALAMAT DEPARTEMEN BARIS 1'
    return address_1

def get_address2(request):
    settings = get_settings()
    address_2 = 'address_2' in settings and settings['address_2'] or 'ALAMAT DEPARTEMEN BARIS 2'
    return address_2

def get_app_name(request):
    settings = get_settings()
    app_name = 'app_name' in settings and settings['app_name'] or 'openSIPKD Application'
    return app_name

def get_gmap_key(request):
    settings = get_settings()
    return 'gmap_key' in settings and settings['gmap_key'] or ''

main_title = 'openSIPKD'
titles = {}

def get_modules(request):
    settings = get_settings()
    if not settings:
        settings = request
    moduls = 'modules' in settings and settings['modules'] and settings['modules'].split(',') or []
    result = {}
    for modul in moduls:
        if modul.find(':')>-1:
            key, val = modul.strip().split(':')
        else:
            key = modul.strip()
            val = '' #key.upper()

        result[key] = val
    return result

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    session_factory = session_factory_from_settings(settings)
    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'

    locale.setlocale(locale.LC_ALL, settings['localization'])
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone

    config = Configurator(settings=settings,
                          root_factory='opensipkd.models.RootFactory',
                          session_factory=session_factory)
    modules = get_modules(settings)
    for module in modules:
        if module=='admin':
            continue
        module = module.replace('/','.')
        mfile = 'opensipkd.'+module
        m = __import__(mfile,globals(), locals(),'main',0)
        m.main(global_config, **settings)

    config.include('pyramid_beaker')
    config.include('pyramid_chameleon')


    authn_policy = AuthTktAuthenticationPolicy('sosecret',
                    callback=group_finder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_request_method(get_company, 'company', reify=True)
    config.add_request_method(get_departement, 'departement', reify=True)
    config.add_request_method(get_ibukota, 'ibukota', reify=True)
    config.add_request_method(get_address, 'address', reify=True)
    config.add_request_method(get_address2, 'address2', reify=True)
    config.add_request_method(get_app_name, 'app_name', reify=True)
    config.add_request_method(get_modules, 'modules', reify=True)
    #config.add_request_method(thousand, 'thousand', reify=True)
    config.add_notfound_view(RemoveSlashNotFoundViewFactory())

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    config.add_static_view('files', settings['static_files'])

    config.add_renderer('csv', '.tools.CSVRenderer')

    routes = DBSession.query(Route.kode, Route.path, Route.nama).\
                filter(Route.type==0).all() #standar route
    for route in routes:
        config.add_route(route.kode, route.path)
        if route.nama:
            titles[route.kode] = route.nama
            
    ############################################################################
    #Custom JSON
    json_renderer = JSON()
    json_renderer.add_adapter(datetime.datetime, lambda v, request: dmy(v))
    json_renderer.add_adapter(datetime.date, lambda v, request: dmy(v))
    json_renderer.add_adapter(decimal.Decimal, lambda v, request: str(v))
    config.add_renderer('json', json_renderer)

    ############################################################################
    # JSON RPC
    config.include('pyramid_rpc.jsonrpc') 
    json_renderer = JSON()
    json_renderer.add_adapter(datetime.datetime, lambda v, request: v.isoformat())
    json_renderer.add_adapter(datetime.date, lambda v, request: v.isoformat())
    config.add_renderer('json_rpc', json_renderer)
    
    routes = DBSession.query(Route.kode, Route.path, Route.nama).\
                filter(Route.type==1).all() # 
    for route in routes:
        config.add_jsonrpc_endpoint(route.kode, route.path, default_renderer="json_rpc")

    ############################################################################
    #config.add_jsonrpc_endpoint('ws_pbb', '/pbb/api', default_renderer="json_rpc")
    #config.add_jsonrpc_endpoint('ws_keuangan', '/ws/keuangan', default_renderer="json_rpc")
    #config.add_jsonrpc_endpoint('ws_user', '/ws/user', default_renderer="json_rpc")
    ############################################################################
    
    ###########################################
    #MAP
    ###########################################
    if 'map' in modules:
        import papyrus
        from papyrus.renderers import GeoJSON, XSD
        
        config.add_request_method(get_gmap_key, 'gmap', reify=True)
        
        config.include(papyrus.includeme)
        config.add_renderer('geojson', GeoJSON())
        config.add_renderer('xsd', XSD())
        config.add_static_view('static_map', 'map/static', cache_max_age=3600)
    
    if 'map/aset' in modules:
        config.add_static_view('static_map_aset', 'map/aset/static', cache_max_age=3600)
    
    if 'map/pbb' in modules:
        config.add_static_view('static_map_pbb', 'map/pbb/static', cache_max_age=3600)
    
    config.scan()
    app = config.make_wsgi_app()
    from paste.translogger import TransLogger
    app = TransLogger(app, setup_console_handler=False)
    return app
    