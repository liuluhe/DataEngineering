# This is the Glue python-shell script to submit a Redshift SQL script to redshift cluster
# Author : Liulu He
# Version: 1.0

import sys
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv,['dbname',
                                    'host',
                                    'port',
                                    'username',
                                    'password',
                                    'sql_script_bucket',
                                    'sql_script_key'])



import psycopg2
con=psycopg2.connect(dbname= args['dbname'], host=args['host'], port= args['port'], user= args['user'], password= args['pwd'])
cur = con.cursor()


import boto3

s3 = boto3.resource('s3')


obj = s3.Object(args['sql_script_bucket'], args['sql_script_key'])
sql_script = obj.get()['Body'].read().decode('utf-8') 

cur.execute(sql_script)
print(cur.fetchall())
cur.close() 
conn.close()