#https://github.com/tensorflow/models/tree/master/slim

if [ ! -d "bin" ]; then
	mkdir "bin"
fi
if [ ! -d "bin/checkpoints" ]; then
	mkdir "bin/checkpoints"
fi

wget http://download.tensorflow.org/models/inception_v1_2016_08_28.tar.gz
tar -xvf inception_v1_2016_08_28.tar.gz
mv inception_v1.ckpt bin/checkpoints
rm inception_v1_2016_08_28.tar.gz
