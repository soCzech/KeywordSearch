#https://github.com/tensorflow/models/tree/master/slim

dirs="bin bin/checkpoints bin/covariance"

for i in ${dirs}
do
    if [ ! -d ${i} ]; then
        mkdir ${i}
    fi
done

wget http://download.tensorflow.org/models/inception_v1_2016_08_28.tar.gz
tar -xvf inception_v1_2016_08_28.tar.gz
mv inception_v1.ckpt bin/checkpoints
rm inception_v1_2016_08_28.tar.gz
