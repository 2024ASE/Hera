# /bin/sh

list=$1

for LIB in `cat ./$list.txt`
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
            docker build --build-arg MY_PARAM="${LIB}_${ver}" $image_dir -t $image_name  
        # else
        #     echo $image_name already exists
        # fi
        wait
        echo $image_name
        docker run --add-host=docker.host:172.17.0.1 -m 256m --cpus=2 --rm $image_name
        wait
        echo "successfully!"
        if [ "$(docker image ls | grep $image_name)" ]
        then
            docker image rm $image_name
        else
            echo "$ver" not exist
        fi
    done
done
echo "successfully!"