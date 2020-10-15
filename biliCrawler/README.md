# BilibiliCrawler

爬取B站的频道信息和相应的视频信息，并做成数据管道最后通过Superset展示。其中用到AWS的服务Glue， Athena。目录包含了爬取代码和ETL的代码
具体部署后的架构图如下：
!(https://github.com/liuluhe/DataEngineering/blob/master/assets/biliarchitect.png)

## 爬取频道数据和视频数据
运行 python 文件 bilibili-url-crawler.py 
运行环境可以在本地或者云上的无服务器服务如AWS Lambda或者AWS Glue
数据会被发送到Amazon Kinesis管道用作实时数据采集到S3，包含频道维度和视频维度两个数据集

## 用Pyspark来做数据处理使数据可读性更好
ETL的部分是基于AWS Glue的一些依赖包，所以需要在Glue上运行或者本地导入[Glue的包](https://docs.aws.amazon.com/zh_cn/glue/latest/dg/aws-glue-programming-etl-libraries.html)

**把JSON和时间分区的时间转化成parquet和mid分区方便查询**
>video-stats-clean-ETL.py

>channel-stats-clean-ETL.py 

**提取频道当前时间点的数据形成快照**
>channel-stats-latest-ETL.py

## Jupyter Notebook版本的ETL逻辑
逻辑和前面pyspark一致，Notebook版加了一些注解，此Notebook可以直接用于Glue 终端节点开发
>ETL-logic-explain.ipynb


