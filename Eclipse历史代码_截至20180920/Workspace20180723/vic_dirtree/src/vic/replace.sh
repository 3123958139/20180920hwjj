#!/bin/bash



o=$1
n=$2

if [ "$o" == "" ]; then
    echo 'old string is null'
    exit -1
fi

if [ "$n" == "" ]; then
    echo 'new string is null'
    exit -1
fi


find ./ -name "*" -type f -maxdepth 4| xargs grep $o | awk -F':' '{print $1}' | xargs sed -i "s/$o/$n/g"



