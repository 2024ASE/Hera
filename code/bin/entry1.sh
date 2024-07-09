# /bin/sh
for LIB in `cat ./all_framework2.txt`
do
    ./download_wheels.sh $LIB
    #./make_image_dir.sh $LIB
done