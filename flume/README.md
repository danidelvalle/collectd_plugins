Collectd Plugin: Apache Flume
=============================

This python script connects to the Apache Flume JSON metric service, pulls down all
of the metrics, and parses them. The metrics that it knows about are then dumped out
in Collectd Text Protocol format.

Installation and Configuration
------------------------------

* Enable the JSON reporting metric service in Flume (http://flume.apache.org/FlumeUserGuide.html#json-reporting)
* Copy flume.py to your Collectd plugin directory
* Then create a configuration file for this plugin.

flume.conf:
   
    LoadPlugin "exec"
    <Plugin exec>
        Exec "nobody" "/tmp/flume.py" "-p" "flume" "-u" "http://localhost:41414/metrics"
    </Plugin>
