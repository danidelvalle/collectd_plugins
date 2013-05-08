#!/bin/bash
#
# Copyright 2013 Nextdoor.com, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Defaults
PORT=2181
HOSTNAME="${COLLECTD_HOSTNAME:-localhost}"
INTERVAL="${COLLECTD_INTERVAL:-5}"

# Generic function for putting a value out there
put_gauge() {
    NAME=$1
    VAL=$2

    # If the VAL or NAME are empty for some reason, we just drop the stat.
    if [ -z $NAME ] || [ -z $VAL ]; then
        return
    fi

    echo "PUTVAL \"$HOSTNAME/zookeeper/gauge-$NAME\" interval=$INTERVAL N:$VAL"
}

# Generic function for putting a value out there
put_counter() {
    NAME=$1
    VAL=$2
    TYPE="${3:-counter}"
    NOW=`date +%s`

    # If the VAL or NAME are empty for some reason, we just drop the stat.
    if [ -z $NAME ] || [ -z $VAL ]; then
        return
    fi

    echo "PUTVAL \"$HOSTNAME/zookeeper/$TYPE-$NAME\" interval=$INTERVAL $NOW:$VAL"
}

# Gather 'global' server stats from the 'srvr' four-letter word.
get_srvr() {
    RAW_STAT=`echo srvr | nc 127.0.0.1 $PORT`

    # Total server connection count
    put_gauge 'connections' `echo $RAW_STAT | egrep -o 'Connections:\ ([0-9]+)' | awk '{print $2}'`

    # Number of outstanding requests
    put_gauge 'outstanding-requests' `echo $RAW_STAT | egrep -o 'Outstanding:\ ([0-9]+)' | awk '{print $2}'`

    # Total number of zNodes registered on this node
    put_gauge 'nodes' `echo $RAW_STAT | egrep -o 'Node count:\ ([0-9]+)' | awk '{print $3}'`

    # Total number of zNodes registered on this node
    LATENCY=`echo $RAW_STAT | egrep -o 'Latency min\/avg\/max:\ ([0-9]+)/([0-9]+)/([0-9]+)' | awk '{print $3}'`
    put_gauge 'latency-min' `echo $LATENCY | awk -F\/ '{print $1}'`
    put_gauge 'latency-avg' `echo $LATENCY | awk -F\/ '{print $2}'`
    put_gauge 'latency-max' `echo $LATENCY | awk -F\/ '{print $3}'`

    # Packets in and out.
    RECEIVED=`echo $RAW_STAT | egrep -o 'Received:\ ([0-9]+)' | awk '{print $2}'`
    SENT=`echo $RAW_STAT | egrep -o 'Sent:\ ([0-9]+)' | awk '{print $2}'`
    put_counter 'traffic' "$RECEIVED:$SENT" 'if_packets'
}

# Gather stats on the total number of 'watches' established
get_wchs() {
    RAW_STAT=`echo wchs | nc 127.0.0.1 $PORT`

    # Total number of watches established
    put_gauge 'local-watches-total' `echo $RAW_STAT | egrep -o 'Total watches:([0-9]+)' | awk -F: '{print $2}'`

    # Number of unique paths being watched
    put_gauge 'local-watches-unique-paths' `echo $RAW_STAT | egrep -o 'watching ([0-9]+) paths' | awk '{print $2}'`
}

# Loop through all of our stat collection functions and print them out on the $INTERVAL
while sleep "${INTERVAL}"; do
    get_srvr
    get_wchs
done

