#! /bin/sh

LIB=$1

for ver in `cat $LIB.txt`
do
    python3 get_releases.py $ver
done