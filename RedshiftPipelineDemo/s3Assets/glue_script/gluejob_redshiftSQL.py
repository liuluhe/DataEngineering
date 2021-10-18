# This is the Glue python-shell script to submit a Redshift SQL script to redshift cluster
# Author : Liulu He
# Version: 1.0

# AWS data wrangler environment preparation. Reference:https://github.com/boto/boto3/issues/2566

import os.path
import subprocess
import sys
import logging
import sys
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv,['dbname',
                                    'cluster_id',
                                    'host',
                                    'port',
                                    'username',
                                    'password',
                                    'sql_script_bucket',
                                    'sql_script_key'])

root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

import boto3
s3 = boto3.resource('s3')


obj = s3.Object(args['sql_script_bucket'], args['sql_script_key'])
sql_script = obj.get()['Body'].read().decode('utf-8') 


########################### Option 1: use PyGreSQL package to make jdbc connection #################
import pg


def get_connection(host,port,db_name,user,password_for_user):
    rs_conn_string = "host=%s port=%s dbname=%s user=%s password=%s" % (
        host, port, db_name, user, password_for_user)

    rs_conn = pg.connect(dbname=rs_conn_string)
    rs_conn.query("set statement_timeout = 1200000")
    return rs_conn


def query(con,statement):
    root.info("Execute SQL %s"%statement)
    res = con.query(statement)
    return res

con1 = get_connection(args['host'],args['port'],args['dbname'],args['username'],args['password'])
res = query(con1,sql_script)

root.info("SQL return is %s"%res)


############################# Option 2: use redshift data API #######################################
# Boto3 version too low, need to upgrade the package
"""
def get_referenced_filepath(file_name, matchFunc=os.path.isfile):
    for dir_name in sys.path:
        candidate = os.path.join(dir_name, file_name)
        if matchFunc(candidate):
            return candidate
    raise Exception("Can't find file: ".format(file_name))

zip_file = get_referenced_filepath("boto3-depends.zip")

subprocess.run(["unzip", zip_file])

# Can't install --user, or without "-t ." because of permissions issues on the filesystem
subprocess.run(["pip3 install --no-index --find-links=. -t . *.whl"], shell=True)

sys.path.insert(0, '/glue/lib/installation')
keys = [k for k in sys.modules.keys() if 'boto' in k]
for k in keys:
    if 'boto' in k:
       del sys.modules[k]

#logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',level=logging.INFO)


root.info('\n')

client = boto3.client('redshift-data')

obj = s3.Object(args['sql_script_bucket'], args['sql_script_key'])
sql_script = obj.get()['Body'].read().decode('utf-8') 

root.info("\nSubmit Redshift query: %s"%sql_script)
# Asynchronous call need to wait for succeeded response
response = client.execute_statement(
    ClusterIdentifier=args['cluster_id'],
    Database=args['dbname'],
    DbUser=args['username'],
    #SecretArn='string',
    Sql=sql_script,
    StatementName='redshift-test',
)

qid = response["Id"]

desc = client.describe_statement(Id=qid)
while True:
    if desc["Status"] == "FINISHED":
        root.info("SQL succeeded: %s"%sql_script)
        break
    elif desc["Status"] =="ABORTED":
        raise Exception("The query run was stopped by the user.")
    elif desc["Status"]=="FAILED":
        raise Exception("The query run was failed with error: %s"%desc["Error"])




###################### Option 3:Use postgres: need extra dependency on postgres ###############################
#import psycopg2
#con=psycopg2.connect(dbname= args['dbname'], host=args['host'], port= args['port'], user= args['user'], password= args['pwd'])
#cur = con.cursor()
#cur.execute(sql_script)
#print(cur.fetchall())
#cur.close() 
#conn.close()

