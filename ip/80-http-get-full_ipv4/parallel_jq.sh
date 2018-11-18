#!/bin/bash
# cat $1 | parallel --gnu -j 8 --nice 10 --pipe './jq_thread' > cdnlist.txt
# ${1##*/}
zcat $1 | parallel --gnu -j 8 --nice 10 --pipe './jq_thread' > "../out/"${1##*/}"_cdn_ips.txt"
