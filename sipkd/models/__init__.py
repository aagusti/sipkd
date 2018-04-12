from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    String,
    SmallInteger
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
import ziggurat_foundations.models
from ziggurat_foundations.models.base import BaseModel
from ziggurat_foundations.models.user import UserMixin
from ziggurat_foundations.models.group import GroupMixin
from ziggurat_foundations.models.group_permission import GroupPermissionMixin
from ziggurat_foundations.models.user_group import UserGroupMixin
from ziggurat_foundations.models.resource import ResourceMixin 
from ziggurat_foundations.models.group_resource_permission import GroupResourcePermissionMixin
from ziggurat_foundations.models.user_permission import UserPermissionMixin
from ziggurat_foundations.models.user_resource_permission import UserResourcePermissionMixin
from ziggurat_foundations.models.external_identity import ExternalIdentityMixin
from ziggurat_foundations import ziggurat_model_init
from pyramid.security import (
    Allow,
    Authenticated,
    Everyone,
    ALL_PERMISSIONS
    )
from ..tools import as_timezone
from .meta import Base
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
#Base = declarative_base()

##############
# Base model #
##############
class CommonModel(object):
    def to_dict(self): # Elixir like
        values = {}
        for column in self.__table__.columns:
            values[column.name] = getattr(self, column.name)
        return values
        
    def from_dict(self, values):
        for column in self.__table__.columns:
            if column.name in values:
                setattr(self, column.name, values[column.name])

    def as_timezone(self, fieldname):
        date_ = getattr(self, fieldname)
        return date_ and as_timezone(date_) or None

class DefaultModel(CommonModel):
    id = Column(Integer, primary_key=True)

    def save(self):
        if self.id:
            DBSession.merge(self)
        else:
            DBSession.add(self)    
        
    @classmethod
    def count(cls):
        return DBSession.query(func.count('id')).scalar()
        
    @classmethod
    def query(cls):
        return DBSession.query(cls)

    @classmethod
    def query_id(cls, id):
        return cls.query().filter_by(id=id)
        
    @classmethod
    def delete(cls, id):
        cls.query_id(id).delete()

class Group(GroupMixin, Base, CommonModel):
    @classmethod
    def query_group_name(cls, group_name):
        return DBSession.query(cls).filter_by(group_name=group_name)

class GroupPermission(GroupPermissionMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base, CommonModel):
    @classmethod
    def _get_by_user(cls, user):
        return DBSession.query(cls).filter_by(user_id=user.id).all()
        
    @classmethod
    def get_by_user(cls, user):
        groups = []
        for g in cls._get_by_user(user):
            groups.append(g.group_id)
        return groups

class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass

class Resource(ResourceMixin, Base):
    pass

class UserPermission(UserPermissionMixin, Base):
    pass

class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass


class User(UserMixin, BaseModel, CommonModel, Base):
    last_login_date = Column(DateTime(timezone=True), nullable=True)
    registered_date = Column(DateTime(timezone=True),
                             nullable=False,
                             default=datetime.utcnow)
    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = self.set_password(password)

    password = property(_get_password, _set_password)

    def get_groups(self):
        return UserGroup.get_by_user(self)

    def last_login_date_tz(self):
        return as_timezone(self.last_login_date)
        
    def registered_date_tz(self):
        return as_timezone(self.registered_date)
        
    def nice_username(self):
        return self.user_name or self.email

    def nip_pbb(self):
        from ..tools import get_settings
        settings = get_settings()
        if self.user_name == 'admin':
            return '060000000000000000'
        
        if "pbb.url" in settings and settings["pbb.url"]:
            from ..pbb.models import pbbDBSession
            from ..pbb.models.pegawai import DatLogin
            row = pbbDBSession.query(DatLogin).\
                    filter_by(nm_login = self.user_name).first()
            if row:
                return row.nip
        return
        
    def kode(self):
        pass
        
        
    @classmethod
    def get_by_email(cls, email):
        return DBSession.query(cls).filter_by(email=email).first()

    @classmethod
    def get_by_name(cls, name):
        return DBSession.query(cls).filter_by(user_name=name).first()        
        
    @classmethod
    def get_by_identity(cls, identity):
        if identity.find('@') > -1:
            return cls.get_by_email(identity)
        return cls.get_by_name(identity)        
        
    @classmethod
    def get_by_token(cls, token):
        return cls.query().filter_by(security_code=token)
    
class ExternalIdentity(ExternalIdentityMixin, Base):
    pass

# It is used when there is a web request.
class RootFactory(object):
    def __init__(self, request):
        self.request = request
        self.__acl__ = [(Allow, 'Admin', ALL_PERMISSIONS), 
                        (Allow, Authenticated, 'view'),]
        if self.request.user and self.request.matched_route:
            rows = DBSession.query(Group.group_name, Route.kode).\
               join(UserGroup).join(GroupRoutePermission).join(Route).\
               filter(UserGroup.user_id==self.request.user.id,
                   Route.kode==self.request.matched_route.name).all()
            if rows:
                for r in rows:
                    self.__acl__.append((Allow, ''.join(['g:',r.group_name]), r.kode))
          
class KodeModel(DefaultModel):
    kode = Column(String(32))
    status = Column(SmallInteger, nullable=False, default=0)
    created  = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated  = Column(DateTime, nullable=True)
    create_uid  = Column(Integer, nullable=True, default=1)
    update_uid  = Column(Integer, nullable=True)
    
    @classmethod
    def query_kode(cls,kode):
        return cls.query().filter_by(kode=kode)
        
    @classmethod            
    def get_by_kode(cls, kode):
        return cls.query_kode(kode).first()
                
    @classmethod
    def get_active(cls):
        return cls.query().filter_by(status=1).all()
    
class UraianModel(DefaultModel):
    nama = Column(String(128))
    status = Column(SmallInteger, nullable=False, default=0)
    created  = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated  = Column(DateTime, nullable=True)
    create_uid  = Column(Integer, nullable=True, default=1)
    update_uid  = Column(Integer, nullable=True)
    
    @classmethod
    def query_nama(cls, nama):
        return cls.query().filter_by(nama=nama)
        
    @classmethod            
    def get_by_nama(cls, nama):
        return cls.query_nama(nama).first()        

class NamaModel(KodeModel):
    nama = Column(String(128))
    
    @classmethod
    def query_nama(cls, nama):
        return cls.query().filter_by(nama=nama)
        
    @classmethod            
    def get_by_nama(cls, nama):
        return cls.query_nama(nama).first()        
        
class Route(Base, NamaModel):
    __tablename__  = 'routes'
    __table_args__ = {'extend_existing':True}
    kode = Column(String(128), unique=True)
    # nama = Column(String(128), unique=True)
    path      = Column(String(256), nullable=False, unique=True)
    status    = Column(Integer, nullable=False)
    type      = Column(SmallInteger, nullable=False, server_default='0')
                                           
class Parameter(Base, NamaModel):
    __tablename__  = 'parameters'
    __table_args__ = {'extend_existing':True}
    value      = Column(String(256), nullable=False)
    
class GroupRoutePermission(Base, CommonModel):
    __tablename__  = 'groups_routes_permissions'
    __table_args__ = {'extend_existing':True,}    
    route_id = Column(Integer, ForeignKey("routes.id"),nullable=False, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"),nullable=False, primary_key=True)
    routes = relationship("Route", backref=backref('routepermission'))
    groups = relationship("Group",backref= backref('grouppermission'))
from .ws_user import WsUser
from targets import Targets
def init_model():
    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource,
                   ExternalIdentity, passwordmanager=None)
