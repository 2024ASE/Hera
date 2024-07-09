# /bin/sh
for LIB in `cat ./all_framework.txt`
do
    for ver in `cat ./versions/$LIB.txt`
    do
        rm -r ./$LIB/
        #rm -f ./$LIB/Dockerfile ./$LIB/*.py ./$LIB/*.sh
        #cp ./code/* ./$LIB/
    done
done