import os
import sys
import transaction
import subprocess
from sqlalchemy import (
    engine_from_config,
    select,
    )
from sqlalchemy.schema import CreateSchema
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    init_model,
    DBSession,
    Base,
    )

from ..models.ar import *
    
import initial_data
from tools import mkdir


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def create_schema(engine, schema):
    sql = select([('schema_name')]).\
          select_from('information_schema.schemata').\
          where("schema_name = '%s'" % schema)
    q = engine.execute(sql)
    if not q.fetchone():
        engine.execute(CreateSchema(schema))

def create_schemas(engine):
    for schema in ['efiling', 'admin', 'aset', 'eis', 'gaji', 'apbd']:
        create_schema(engine, schema)

def read_file(filename):
    f = open(filename)
    s = f.read()
    f.close()
    return s

def main(argv=sys.argv):
    def alembic_run(ini_file):
        s = read_file(ini_file)
        s = s.replace('{{db_url}}', settings['sqlalchemy.url'])
        f = open('alembic.ini', 'w')
        f.write(s)
        f.close()
        subprocess.call(command)   
        os.remove('alembic.ini')

    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    # Create Ziggurat tables
    bin_path = os.path.split(sys.executable)[0]
    alembic_bin = os.path.join(bin_path, 'alembic') 
    command = (alembic_bin, 'upgrade', 'head')    
    alembic_run('alembic.ini.tpl')
    alembic_run('alembic_upgrade.ini.tpl')
    # Insert data
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    init_model()
    #create_schemas(engine)
    Base.metadata.create_all(engine)
    initial_data.insert()
    transaction.commit()
