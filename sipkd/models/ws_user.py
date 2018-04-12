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
    
from ..models import DefaultModel, Base, DBSession
class WsUser(Base, DefaultModel):
    __tablename__  = 'user_ws'
    __table_args__ = {'extend_existing':True}
    user_name = Column(String(128), nullable=False)
    user_password = Column(String(256), nullable=False)
    email = Column(String(100), nullable=False)
    status = Column(SmallInteger, nullable=False)
    last_login_date = Column(DateTime(timezone=False))
    registered_date = Column(DateTime(timezone=False))
    
    @classmethod
    def query(cls):
        return DBSession.query(cls)
        
    @classmethod
    def query_name(cls, user_name):
        return cls.query().filter_by(user_name=user_name)
    
    @classmethod
    def query_email(cls, email):
        return cls.query().filter_by(email=email)
        
    @classmethod
    def query_identity(cls, identity):
        if identity.find('@') > -1:
            return cls.query_email(identity)
        return cls.query_name(identity)

    @classmethod
    def by_id(cls, user_id, db_session=None):
        """

        .. deprecated:: 0.8

        :param user_id:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.by_id(user_id=user_id, db_session=db_session)

    @classmethod
    def by_user_name(cls, user_name, db_session=None):
        """

        .. deprecated:: 0.8

        :param user_name:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.by_user_name(user_name=user_name,
                                        db_session=db_session)

    @classmethod
    def by_user_name_and_security_code(cls, user_name, security_code,
                                       db_session=None):
        """

        .. deprecated:: 0.8

        :param user_name:
        :param security_code:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.by_user_name_and_security_code(
            user_name=user_name, security_code=security_code,
            db_session=db_session)

    @classmethod
    def by_user_names(cls, user_names, db_session=None):
        """

        .. deprecated:: 0.8

        :param user_names:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.by_user_names(user_names=user_names,
                                         db_session=db_session)

    @classmethod
    def user_names_like(cls, user_name, db_session=None):
        """

        .. deprecated:: 0.8

        :param user_name:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.user_names_like(user_name=user_name,
                                           db_session=db_session)

    @classmethod
    def by_email(cls, email, db_session=None):
        """

        .. deprecated:: 0.8

        :param email:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.by_email(email=email,
                                    db_session=db_session)

    @classmethod
    def by_email_and_username(cls, email, user_name, db_session=None):
        """

        .. deprecated:: 0.8

        :param email:
        :param user_name:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.by_email_and_username(email=email,
                                                 user_name=user_name,
                                                 db_session=db_session)

    @classmethod
    def users_for_perms(cls, perm_names, db_session=None):
        """

        .. deprecated:: 0.8

        :param perm_names:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return UserService.users_for_perms(perm_names=perm_names,
                                           db_session=db_session)
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

