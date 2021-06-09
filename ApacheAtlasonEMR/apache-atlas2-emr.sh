#!/bin/sh

sudo mkdir /apache && sudo chown hadoop.hadoop /apache
 

# download Atlas 1.0.0
# sudo curl https://s3.amazonaws.com/apache-atlas-setup-on-emr/apache-atlas-1.0.0-bin.tar.gz -o /tmp/apache-atlas-1.0.0-bin.tar.gz && sudo tar xvpfz /tmp/apache-atlas-1.0.0-bin.tar.gz -C /apache
# download Atlas 2.1.0
# sudo curl https://aws-ningxia-demo.s3.cn-northwest-1.amazonaws.com.cn/emr-atlas/assets/apache-atlas-2.1.0-bin.tar.gz -o /tmp/apache-atlas-2.1.0-bin.tar.gz && sudo tar xvpfz /tmp/apache-atlas-2.1.0-bin.tar.gz -C /apache
aws s3 cp s3://aws-ningxia-demo/emr-atlas/assets/apache-atlas-2.1.0-bin.tar.gz /tmp/apache-atlas-2.1.0-bin.tar.gz && sudo tar xvpfz /tmp/apache-atlas-2.1.0-bin.tar.gz -C /apache

sudo curl https://s3.amazonaws.com/apache-atlas-setup-on-emr/kafka_2.11-1.1.0.tgz -o /tmp/kafka_2.11-1.1.0.tgz && sudo tar xvpfz /tmp/kafka_2.11-1.1.0.tgz -C /apache
sudo yum install -y https://s3.amazonaws.com/apache-atlas-setup-on-emr/jdk-8u171-linux-x64.rpm

# Create symlinks
sudo ln -s /apache/kafka_2.11-1.1.0 /apache/kafka
sudo ln -s /apache/apache-atlas-2.1.0 /apache/atlas

# Change default port for zookeeper and kafka
sudo sed -i 's/clientPort=2181/clientPort=3000/' /apache/kafka/config/zookeeper.properties
sudo sed -i 's/zookeeper.connect=localhost:2181/zookeeper.connect=localhost:3000/' /apache/kafka/config/server.properties

#set these variables in hadoop user's bash profile
sudo cat << EOL >> /home/hadoop/.bash_profile

export JAVA_HOME=/usr/java/jdk1.8.0_171-amd64/
export MANAGE_LOCAL_HBASE=false
export MANAGE_LOCAL_SOLR=true
export HIVE_HOME=/usr/lib/hive
export HIVE_CONF_DIR=/usr/lib/hive/conf
export SQOOP_HOME=/usr/lib/sqoop
export PATH=$PATH:$SQOOP_HOME/bin
export HADOOP_HOME=/usr/lib/hadoop
export HBASE_HOME=/usr/lib/hbase
EOL

export JAVA_HOME=/usr/java/jdk1.8.0_171-amd64/
sudo /apache/kafka/bin/zookeeper-server-start.sh -daemon /apache/kafka/config/zookeeper.properties
sudo /apache/kafka/bin/kafka-server-start.sh -daemon /apache/kafka/config/server.properties

# Create a symlink in native hive's conf directory
sudo ln -s /apache/atlas/conf/atlas-application.properties /usr/lib/hive/conf/atlas-application.properties

# add hive hook in hiveserver2 /etc/hive/conf/hiveserver2-site.xml
# Ensure that following is present:
#  <property>
#    <name>hive.exec.post.hooks</name>
#    <value>org.apache.atlas.hive.hook.HiveHook</value>
#  </property>
#sudo cp /etc/hive/conf/hive-site.xml /etc/hive/conf/hive-site.xml.orig
#sudo sed -i "s#</configuration>#   <property>\n     <name>hive.exec.post.hooks</name>\n     <value>org.apache.atlas.hive.hook.HiveHook</value>\n   </property>\n\n</configuration>#" /etc/hive/conf/hive-site.xml || mv /etc/hive/conf/hive-site.xml.orig /etc/hive/conf/hive-site.xml

# Prepare Hive env
#cd /usr/lib/hive/lib
cd /usr/lib/hive/auxlib
sudo ln -s /apache/atlas/hook/hive/atlas-plugin-classloader-2.1.0.jar
sudo ln -s /apache/atlas/hook/hive/hive-bridge-shim-2.1.0.jar
for i in /apache/atlas/hook/hive/atlas-hive-plugin-impl/*; do sudo ln -s $i; done

sudo systemctl restart hive-server2

# Prepare Hbase env
sudo ln -s /apache/atlas/conf/atlas-application.properties /usr/lib/hbase/conf/atlas-application.properties
sudo ln -s /apache/atlas/hook/hbase/* /usr/lib/hbase/lib/

#Prepare Sqoop env

#mkdir /usr/lib/sqoop/
#sudo curl https://mirrors.bfsu.edu.cn/apache/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz -o /tmp/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz && sudo tar xvpfz /tmp/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz -C /tmp/ && sudo mv /tmp/sqoop-1.4.7.bin__hadoop-2.6.0 /usr/lib/sqoop
#cd $SQOOP_HOME/conf
#sudo mv sqoop-env-template.sh sqoop-env.sh
#sudo curl http://ftp.ntu.edu.tw/MySQL/Downloads/Connector-J/mysql-connector-java-8.0.23.tar.gz -o /tmp/mysql-connector-java-8.0.23.tar.gz && sudo tar xvpfz /tmp/mysql-connector-java-8.0.23.tar.gz -C /tmp/ && sudo mv /tmp/mysql-connector-java-8.0.23/mysql-connector-java-8.0.23.jar /usr/lib/sqoop/lib


sudo ln -s /apache/atlas/conf/atlas-application.properties /usr/lib/sqoop/conf/atlas-application.properties
sudo ln -s /apache/atlas/hook/sqoop/* /usr/lib/sqoop/lib/

#Prepare Spark env
aws s3 cp s3://aws-ningxia-demo/emr-atlas/assets/spark-atlas-connector-assembly-0.1.0-SNAPSHOT.jar ~/
sudo ln -s /apache/atlas/conf/atlas-application.properties /usr/lib/spark/conf/atlas-application.properties

# need to replace solr start code to add -force
aws s3 cp s3://aws-ningxia-demo/emr-atlas/assets/atlas2.1.0/bin/atlas_config.py ~/
sudo mv ~/atlas_config.py /apache/atlas/bin/atlas_config.py

# To run Apache Atlas with local Apache HBase & Apache Solr instances that are started/stopped along with Atlas start/stop, run following commands:
sudo sed -i 's?#export JAVA_HOME=?export JAVA_HOME=/usr/java/jdk1.8.0_171-amd64?' /apache/atlas/conf/atlas-env.sh
sudo sed -i 's/export MANAGE_LOCAL_HBASE=true/export MANAGE_LOCAL_HBASE=false/' /apache/atlas/conf/atlas-env.sh
sudo /apache/atlas/bin/atlas_start.py && sudo /apache/atlas/bin/atlas_stop.py && sudo /apache/atlas/bin/atlas_start.py


