#!/bin/bash
# cat $1 | parallel --gnu -j 8 --nice 10 --pipe './jq_thread' > > "../out/"${1##*/}"_cdn_ips.txt"
# ${1##*/}
cat $1 | parallel --gnu -j 8 --nice 10 --pipe 'python read_sonar_http_data.py'
