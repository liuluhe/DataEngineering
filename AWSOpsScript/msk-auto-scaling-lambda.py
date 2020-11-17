import json
import boto3
import os



def lambda_handler(event, context):
    client = boto3.client('kafka',region_name=os.environ['regionName'])
    response = client.list_clusters(ClusterNameFilter=os.environ['clusterNamePrefix'],MaxResults=1)
    clusterarn = response['ClusterInfoList'][0]['ClusterArn']
    clusterversion = response['ClusterInfoList'][0]['CurrentVersion']
    currentStorage = response['ClusterInfoList'][0]['BrokerNodeGroupInfo']['StorageInfo']['EbsStorageInfo']['VolumeSize']
    targetStorage = currentStorage + int(os.environ['deltaStorageGB'])
    
    response = client.update_broker_storage(
        ClusterArn = clusterarn,
        CurrentVersion=clusterversion,
        TargetBrokerEBSVolumeInfo=[
            {
                'KafkaBrokerNodeId': 'All',
                'VolumeSizeGB': targetStorage
            },
        ]
    )

   
    return targetStorage
