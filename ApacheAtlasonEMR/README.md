# ApacheAtlasonEMR

Apache Atlas是管理Hadoop组件的数据治理组件，具体的见官网：https://atlas.apache.org/#/
Apache Atlas具有数据字典、搜索、标签、表血缘等数据治理功能，本项目介绍如何在Amazon EMR服务上搭载一个单体的Atlas服务实现其数据管理功能。使用的环境如下：
Apache Atlas 2.1.0 （只支持Spark 2.x和Hbase 2.x）
Amazon EMR 6.0.0
Spark 2.4.4
Hbase 2.2.3
Hive 3.1.2
AWS Glue Catalog

## 下载Apache Atlas启动脚本
以上CLI安装Atlas主要靠的是参数--steps中的启动脚本，启动脚本是以下文件

>apache-atlas2-emr.sh

请把这个脚本放到Amazon S3中并开放公网访问。这样S3就会给这个文件生成一个https地址如
https://xxx.s3.cn-northwest-1.amazonaws.com.cn/apache-atlas2-emr.sh
需要把这个地址填入以下的CLI中--steps 中

## 安装[AWS CLI](https://aws.amazon.com/cli/)后运行以下命令可以起一个带有Atlas的EMR集群

```
aws emr create-cluster --termination-protected \
--applications Name=Hive Name=Spark Name=HBase Name=Hue Name=Hadoop Name=ZooKeeper \
--tags 'Name=EMR Atlas2.1 Cluster' \
--ec2-attributes '{"KeyName":"test-china-ningxia","InstanceProfile":"EMR_EC2_DefaultRole","SubnetId":"subnet-3ba58c71","EmrManagedSlaveSecurityGroup":"sg-025fa4959b6d63cb6","EmrManagedMasterSecurityGroup":"sg-0fd2aa0aca5867a58"}' \
--release-label emr-6.0.0 \
--log-uri 's3n://aws-ningxia-demo/emr-atlas/emrlog/' \
--steps '[{"Args":["bash","-c","curl <之前步骤中的apache-atlas2-emr.sh https地址> -o /tmp/script.sh; chmod +x /tmp/script.sh; /tmp/script.sh"],"Type":"CUSTOM_JAR","ActionOnFailure":"CONTINUE","Jar":"command-runner.jar","Properties":"=","Name":"AtlasStep"}]' \
--instance-groups '[{"InstanceCount":2,"EbsConfiguration":{"EbsBlockDeviceConfigs":[{"VolumeSpecification":{"SizeInGB":50,"VolumeType":"gp2"},"VolumesPerInstance":4}]},"InstanceGroupType":"CORE","InstanceType":"m5.2xlarge","Name":"Core"},{"InstanceCount":1,"EbsConfiguration":{"EbsBlockDeviceConfigs":[{"VolumeSpecification":{"SizeInGB":100,"VolumeType":"gp2"},"VolumesPerInstance":2}]},"InstanceGroupType":"MASTER","InstanceType":"m5.xlarge","Name":"Master"}]' \
--configurations '[{"Classification":"hbase-site","Properties":{"hbase.coprocessor.master.classes":"org.apache.atlas.hbase.hook.HBaseAtlasCoprocessor"}},{"Classification":"hive-site","Properties":{"hive.exec.post.hooks":"org.apache.atlas.hive.hook.HiveHook"}},{"Classification":"hiveserver2-site","Properties":{"hive.exec.post.hooks":"org.apache.atlas.hive.hook.HiveHook"}}]' \
--service-role EMR_DefaultRole \
--name 'AtlasEMRCluster' \
--scale-down-behavior TERMINATE_AT_TASK_COMPLETION \
--region cn-northwest-1
```


**配置参数部分 --configurations**
EMR可以通过--configurations来配置参数，Atlas是侵入式的监控计算引擎，所以修改相应组件的配置
相应配置如下，配置了Glue Catalog和Atlas Hook
```json
[
  {
    "Classification": "hbase-site",
    "Properties": {
      "hbase.coprocessor.master.classes": "org.apache.atlas.hbase.hook.HBaseAtlasCoprocessor"
    }
  },
  {
    "Classification": "hive-site",
    "Properties": {
      "hive.exec.post.hooks": "org.apache.atlas.hive.hook.HiveHook",
      "hive.metastore.client.factory.class":"com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
    }
  },
  {
    "Classification": "spark-hive-site",
    "Properties": {
      "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
    }
  },
  {
    "Classification": "hiveserver2-site",
    "Properties": {
      "hive.exec.post.hooks": "org.apache.atlas.hive.hook.HiveHook"
    }
  }
]

```
## 简单测试Atlas功能的demo

**下载测试数据并上传到S3**
下载以下路径中的数据并上传到S3中的catalog_sales文件夹

>sample_data/catalog_sales/

并把S3的路径填入以下的建表语句类似s3://xxxx/catalog_sales

**使用Hive DDL建表**
SSH到EMR主节点后，使用beeline -u jdbc:hive2://localhost:10000 -n hadoop进入Hive控制台
```SQL
CREATE EXTERNAL TABLE catalog_sales(
  cs_ship_customer_sk bigint , 
  cs_promo_sk bigint , 
  cs_net_paid_inc_ship_tax double, 
  cs_sales_price double, 
  cs_ship_hdemo_sk bigint, 
  cs_catalog_page_sk bigint, 
  cs_bill_hdemo_sk bigint, 
  cs_ship_mode_sk bigint, 
  cs_ship_addr_sk bigint, 
  cs_ship_cdemo_sk bigint, 
  cs_net_paid double, 
  cs_bill_cdemo_sk bigint, 
  cs_ext_tax_double double, 
  cs_warehouse_sk bigint, 
  cs_call_center_sk bigint, 
  cs_bill_customer_sk bigint, 
  cs_net_paid_inc_ship double, 
  cs_sold_time_sk bigint, 
  cs_quantity bigint, 
  cs_ship_date_sk bigint, 
  cs_ext_list_price double, 
  cs_sold_date_sk bigint, 
  cs_ext_discount_amt double, 
  cs_ext_ship_cost double, 
  cs_net_profit_double double, 
  cs_list_price double, 
  cs_item_sk bigint, 
  cs_coupon_amt double, 
  cs_wholesale_cost double, 
  cs_bill_addr_sk bigint, 
  cs_ext_wholesale_cost double, 
  cs_ext_sales_price double, 
  cs_order_number bigint, 
  cs_net_paid_inc_tax double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://xxxx/catalog_sales'
```
**使用Hive SQL做ETL生成一张新表**

```SQL
create table catalog_sales_hivesql as
select cs_ship_customer_sk
  ,cs_ship_date_sk
  ,cs_item_sk
  ,cs_sales_price
  ,cs_order_number
from default.catalog_sales;

```
**使用Spark SQL做ETL生成一张新表**
在EMR上使用spark-sql进入控制台
```
spark-sql --jars spark-atlas-connector-assembly-0.1.0-SNAPSHOT.jar \
--conf spark.extraListeners=com.hortonworks.spark.atlas.SparkAtlasEventTracker \
--conf spark.sql.queryExecutionListeners=com.hortonworks.spark.atlas.SparkAtlasEventTracker \
--conf spark.sql.streaming.streamingQueryListeners=com.hortonworks.spark.atlas.SparkAtlasStreamingQueryEventTracker
```

运行以下Spark SQL建一张新表
```SQL
create database spark_test Location 'hdfs:///user/spark/warehouse/';
create table spark_test.catalog_sales_sparksql as
select cs_warehouse_sk
  ,sum(cs_quantity)
  ,sum(cs_sales_price)
  ,min(cs_net_profit_double)
  ,max(cs_wholesale_cost)
from default.catalog_sales
group by cs_warehouse_sk;
```

**测试Hbase的元数据同步**
使用hbase shell进入Hbase控制台运行
```SQL
create 'emp', 'personal data', 'professional data'
put 'emp','1','personal data:name','Jack'
put 'emp','1','personal data:city','Denver'
put 'emp','1','professional data:designation','Manager'
put 'emp','1','professional data:salary','30000'

put 'emp','2','personal data:name','Mary'
put 'emp','2','personal data:city','Irvine'
put 'emp','2','professional data:designation','CI'
put 'emp','2','professional data:salary','10000'
put 'emp','2','professional data:phone','123456'
```

**登录Atlas查看数据血缘**

使用EMR主节点的公有域名登录Atlas
http://<EMR master DNS>:21000
用户名和密码都是admin

![image](https://github.com/liuluhe/DataEngineering/blob/master/assets/atlasdatalineage.png)