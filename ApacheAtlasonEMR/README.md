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





