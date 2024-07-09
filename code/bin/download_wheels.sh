#! /bin/sh

pip download pymongo -d ./wheels/common/
pip download parso -d ./wheels/common/

LIB=$1
echo $LIB
for ver in `cat ./versions/$LIB.txt`
do
    mkdir -p ./wheels/$LIB/$ver/
    pip download $LIB==$ver -d ./wheels/$LIB/$ver/
done
