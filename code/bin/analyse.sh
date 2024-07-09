# /bin/sh
for LIB in `cat ./all_framework.txt`
do
    for ver in `cat ./versions/$LIB.txt`
    do
        image_name="${LIB}_api_extract-$ver"
        # if [ ! "$(docker image ls | grep "$image_name ")" ]
        # then
            image_dir="./$LIB/image/$ver"
            rm -f $image_dir/Dockerfile ./image/$ver/*.py ./image/$ver/*.sh
            cp ./$LIB/Dockerfile $image_dir
            cp ./$LIB/*.py $image_dir
            cp ./$LIB/*.sh $image_dir
            docker build --build-arg MY_PARAM="${LIB}_${ver}" $image_dir -t $image_name & 
        # else
        #     echo $image_name already exists
        # fi
    done
    wait
    for ver in `cat ./versions/$LIB.txt`
    do
        image_name="${LIB}_api_extract-$ver"
        echo $image_name
        docker run --add-host=docker.host:172.17.0.1 -m 256m --cpus=2 --rm $image_name &
    done
    wait
    echo "successfully!"
    ./cleanup_images.sh $LIB
    echo $LIB
done
echo "successfully!"