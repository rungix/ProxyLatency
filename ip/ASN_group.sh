#!/bin/sh
cat $1 | awk '{print $2;}' | sort | uniq -c | sort -n -r
