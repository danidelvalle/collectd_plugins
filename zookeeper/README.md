Collectd Plugin: Apache Zookeeper
=================================

This simple shell script runs in a loop and gathers data from the Apache Zookeeper
service running locally using the 'four letter words.' The stats are printed using
the Collectd Text Protocol.

Installation and Configuration
------------------------------

First, copy zookeeper.sh to your Collectd plugin directory
Then, add this to your collectd configuration file:
   
    LoadPlugin "exec"
    <Plugin exec>
        Exec "nobody" "/etc/collectd/conf/plugins/zookeeper.sh"
    </Plugin>
