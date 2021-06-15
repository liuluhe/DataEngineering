# This is the Glue python-shell script to submit a Redshift SQL script to redshift cluster
# Author : Liulu He
# Version: 1.0

# AWS data wrangler environment preparation. Reference:https://github.com/boto/boto3/issues/2566

import os.path
import subprocess
import sys

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

import boto3
print('boto3 version')
print(boto3.__version__)

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


import boto3
client = boto3.client('redshift-data')
s3 = boto3.resource('s3')


obj = s3.Object(args['sql_script_bucket'], args['sql_script_key'])
sql_script = obj.get()['Body'].read().decode('utf-8') 

#cur.execute(sql_script)
#print(cur.fetchall())
#cur.close() 
#conn.close()

response = client.execute_statement(
    ClusterIdentifier=args['cluster_id'],
    Database=args['dbname'],
    DbUser=args['username'],
    #SecretArn='string',
    Sql=sql_script,
    StatementName='redshift-test',
)

#import psycopg2
#con=psycopg2.connect(dbname= args['dbname'], host=args['host'], port= args['port'], user= args['user'], password= args['pwd'])
#cur = con.cursor()

