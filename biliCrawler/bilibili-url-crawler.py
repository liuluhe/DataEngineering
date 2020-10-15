# -*- coding:utf-8 -*-
import json
import requests
import time
from datetime import datetime,timedelta
import boto3
import re

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
}
kinesis_client = boto3.client('kinesis', region_name='ap-northeast-1')
video_stats_stream_name = 'video-stats-stream'
owner_stats_stream_name = 'owner-stats-stream'

s3 = boto3.client('s3',region_name='ap-northeast-1')
bucket_name = 'aws-demo-live-code-demo'
prefix = 'data/danmu'

def get_videos_stats(mid, n,batch):
    iterator = n/20 + 2
    for i in range(1, min(5,iterator)):
        url = 'https://api.bilibili.com/x/space/arc/search?mid=%s&pn=%s&ps=20&jsonp=jsonp' % (mid, i)
        r = requests.get(url, headers)
        result = {}
        text = json.loads(r.text)

        res = text['data']['list']['vlist']
        for item in res:

            video_url = 'https://api.bilibili.com/x/web-interface/view?bvid=%s' %(item['bvid'])
            rr = requests.get(video_url, headers)
            t = json.loads(rr.text)
            result['mid']=mid
            result['owner']=t['data']['owner']['name']
            result['title'] = t['data']['title']
            result['duration'] = t['data']['duration']
            result['bv'] = str(item['bvid'])
            result['views'] = t['data']['stat']['view']
            result['favorites'] = t['data']['stat']['favorite']
            result['likes'] = t['data']['stat']['like']
            result['dislike'] = t['data']['stat']['dislike']
            result['coins'] = t['data']['stat']['coin']
            result['cid']=t['data']['cid']
            result['created_date'] = format(datetime.fromtimestamp(item['created']))
            result['crawl_date'] = batch
            result['danmu_count'] = get_danmu(t['data']['cid'],str(item['bvid']),mid)
            
            put_to_stream(str(item['bvid']), video_stats_stream_name, result)
            
           
 
def get_danmu(cid,bv,mid):
    danmu_url = 'https://api.bilibili.com/x/v1/dm/list.so?oid=%s' % (cid)
    r = requests.get(danmu_url, headers)
    r.encoding='UTF-8'

    xml = re.sub(r'(\<\?xml.*</source>)|(</i>)', '', r.text.encode('UTF-8'))
    result = re.sub(r'<d[^<]*>', '', xml).replace('</d>','\n')

    n = xml.count("</d>")

    file_name = prefix + '/' + mid + '/' + bv + '.txt'
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=bytes(result))
    return n
    
    
def get_up_stats(mid,batch):
    following_url = 'https://api.bilibili.com/x/relation/stat?vmid=%s&jsonp=jsonp' %(mid)
    result = {}
    r = requests.get(following_url, headers)
    text = json.loads(r.text)
    result['following']=text['data']['following']
    result['follower'] = text['data']['follower']

    video_list_url = 'https://api.bilibili.com/x/space/arc/search?mid=%s&pn=1&ps=%s&jsonp=jsonp' % (mid, 1)
    r = requests.get(video_list_url, headers)
    text = json.loads(r.text)
    result['video_counts'] = text['data']['page']['count']

    result['tag'] = []
    for item in text['data']['list']['tlist']:
        new = {}
        k = text['data']['list']['tlist'][item]['name']
        v = text['data']['list']['tlist'][item]['count']
        new[k]=v
        result['tag'].append(new)

    # crawling frequency is hourly
    result['crawl_date'] = batch
    result['mid'] = mid # use https://space.bilibili.com/{mid} get to the main page
    put_to_stream(mid,owner_stats_stream_name,result)
    return result

def put_to_stream(partition_key, kinesis_name, payload):

    put_response = kinesis_client.put_record(
                        StreamName=kinesis_name,
                        Data=json.dumps(payload,encoding='UTF-8', ensure_ascii=False)+'\n',
                        PartitionKey=partition_key)


if __name__ == '__main__':
    
    mid_list = ['418158141','18202105','456606920']
    batch = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    for mid in mid_list:
        up = get_up_stats(mid,batch)
        get_videos_stats(mid,up['video_counts'],batch)
    
