#!/usr/bin/python
"""

Copyright 2013 Nextdoor.com, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------

This is a simple JSON-parsing collectd monitoring script for Flume. Flume by
default provides a simple URL (http://localhost:<port>/metric) that can be
accessesed to pull down detailed runtime stats of the various Source, Sink
and Channel configs in your Flume agent.

Unfortunately the Collectd curl_json plugin cannot read this JSON output
because Flume prints out all of the numbers as strings rather than integers,
effectively breaking the curl_json plugin entirely.

This plugin uses a static list of known metric-types that are supported and
retrieves them every XX seconds (where XX is the interval configured by
Collectd). Metrics are printed out in the standard Collectd PUTVAL format.

Each Source, Sink or Channel will provide the following metrics:
    JSON:
        {
            "CHANNEL.fc1": {
                "ChannelCapacity": "1000000",
                "ChannelFillPercentage": "0.0",
                "ChannelSize": "0",
                "EventPutAttemptCount": "0",
                "EventPutSuccessCount": "0",
                "EventTakeAttemptCount": "3203",
                "EventTakeSuccessCount": "0",
                "StartTime": "1367940231789",
                "StopTime": "0",
                "Type": "CHANNEL"
            }
        }

    Metrics:
        PUTVAL "localhost/flume-CHANNEL-fc1/gauge-ChannelSize" 1367956296:0.0
        PUTVAL "localhost/flume-CHANNEL-fc1/counter-EventPutAttemptCount" interval=60 1367956296:0
        PUTVAL "localhost/flume-CHANNEL-fc1/gauge-ChannelFillPercentage" 1367956296:0.0
        PUTVAL "localhost/flume-CHANNEL-fc1/counter-EventTakeSuccessCount" interval=60 1367956296:0
        PUTVAL "localhost/flume-CHANNEL-fc1/counter-EventTakeAttemptCount" interval=60 1367956296:3203
        PUTVAL "localhost/flume-CHANNEL-fc1/gauge-ChannelCapacity" 1367956296:1000000.0
        PUTVAL "localhost/flume-CHANNEL-fc1/counter-EventPutSuccessCount" interval=60 1367956296:0

Collectd Configuration File Example:
    LoadPlugin "exec"
    <Plugin exec>
        Exec "nobody" "/tmp/flume.py" "-p" "flume" "-u" "http://localhost:41414/metrics"
    </Plugin>
"""

__author__ = 'matt@nextdoor.com (Matt Wise)'

from optparse import OptionParser
import json
import os
import time
import urllib2

METRICS = {
    # Channel Metrics
    'ChannelSize': 'gauge',
    'ChannelCapacity': 'gauge',
    'ChannelFillPercentage': 'gauge',
    'EventPutAttemptCount': 'counter',
    'EventTakeSuccessCount': 'counter',
    'EventTakeAttemptCount': 'counter',
    'EventPutSuccessCount': 'counter',
    'ConnectionFailedCount': 'counter',

    # Sink Metrics
    'ConnectionFailedCount': 'counter',
    'ConnectionClosedCount': 'counter',
    'ConnectionCreatedCount': 'counter',
    'EventDrainAttemptCount': 'counter',
    'BatchCompleteCount': 'counter',
    'EventDrainSuccessCount': 'counter',
    'BatchUnderflowCount': 'counter',
    'BatchEmptyCount': 'counter',

    # Source Metrics
    'EventReceivedCount': 'counter',
    'OpenConnectionCount': 'counter',
    'AppendBatchReceivedCount': 'counter',
    'AppendBatchAcceptedCount': 'counter',
    'EventAcceptedCount': 'counter',
    'AppendAcceptedCount': 'counter',
    'AppendReceivedCount': 'counter',
}

usage = "usage: %prog -p <prefix> -u url"
parser = OptionParser(usage=usage, add_help_option=True)
parser.set_defaults(verbose=True)
parser.add_option("-p", "--prefix", dest="prefix",
                  help="Prefix to use for the Collectd stats")
parser.add_option("-u", "--url", dest="url",
                  help="URL to pull JSON from")
parser.add_option("-H", "--hostname", dest="hostname",
                  default=os.environ.get('COLLECTD_HOSTNAME', 'localhost'),
                  help="Hostname to pass stats as")
parser.add_option("-i", "--interval", dest="interval",
                  default=os.environ.get('COLLECTD_INTERVAL', 60),
                  help="Frequency to get data")
parser.add_option("-k", "--keylevel", dest="keylevel",
                  default=1,
                  help="Level of JSON to use for KEYs")


(options, args) = parser.parse_args()

# Check if an action was passed at all
if not (options.prefix and options.url):
    parser.error("must not specify both --prefix and --url in the same command line")


# Map of specific Flume metric types to their graph and data formats.
def print_metric(group, name, value):
    """Print specific Flume metric names to Collectd graph types and formats.

    args:
        group: String representing the group name of the metric
        name: String representing the metric name
        value: The value supplied with that metric
    """
    prefix = 'PUTVAL "%s/%s' % (options.hostname, options.prefix)
    clean_group_name = group.replace('.', '-')

    try:
        if METRICS[name] is 'counter':
            print '%s-%s/counter-%s" interval=%d %d:%d' % (prefix, clean_group_name,
                                                           name, int(options.interval),
                                                           int(time.time()), int(value))
        if METRICS[name] is 'gauge':
            print '%s-%s/gauge-%s" %d:%s' % (prefix, clean_group_name,
                                             name, int(time.time()), float(value))
    except KeyError:
        # If this is not a supported metric, then don't return anything.
        pass


def main():
    while True:
        response = urllib2.urlopen(options.url)
        obj = json.loads(response.read())

        # First level of the JSON is the list of sources, channels and sinks.
        for group, data in obj.iteritems():
            # Second level of the JSON is the data for each group we care about.
            for key, value in data.iteritems():
                # Generate a collectd-happy version of the metric name
                print_metric(group, key, value)

        time.sleep(int(options.interval))

main()
