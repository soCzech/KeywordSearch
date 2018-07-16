Python Scripts
==============

The structure of the scripts is the following:
- ***common\_utils***: Scripts responsible for loading and storing data, etc.
- ***models***: Scripts containing neural network definitions, image preprocessing, etc.
- ***processing***: Runnable scripts used for dataset creation, training and classification.
- ***simulations***: Runnable scripts used for user simulations.


## Requirements
The scripts are writen for `Python 3.x` with following additional packages needed:
- `numpy`: vector ops
- `tensorflow`: neural network framework
- `sklearn`: various machine learning algorithms such as PCA and k-means
- `PIL`: image processing
- `matplotlib`: graphs
- `nltk`: WordNet structure

We recommend to use *Anaconda* as an virtual environment.
If possible also `tensorflow` with CUDA support is recommended (see TensorFlow website).
The scripts were tested with `tensorflow=1.6`.

## Dataset Creation
ImageNet classes need to be downloaded from the internet using `processing/download_dataset.sh`.
Note that you need to register on the ImageNet website in order to be able to download the dataset.
Also note that the dataset can take in order of 1TB of memory and at least multiple days to download.

`processing/select_classes.py` can be then run to cluster individual classes and to create
html page of WordNet DAG for each cluster. User can then select classes that will be
used for the network.

`processing/create_dataset.py` then creates tfrecords needed for network training.
Do not forget to create train and validation datasets separately.
It also creates label file needed further for the application UI that can
also be created separately by `processing/create_labels.py` script.


## Network Training
The network is trained by `processing/train.py`.
To run only validation, use `processing/validation.py` script.

## Classification
Image classification given a trained model can be done by `processing/classify.py`.
The script creates following files:
- `.annotation`: Used to created inverted index.
- `.deep-features`: Used for simulations for similarity reranking.
                    It contains network's last layer activation values.
- `.softmax`: Contains netwok's output (softmax) values.
              Used for simulations instead of the annotation file to simulate different thresholds.
- `.sumX`: Contains sum of all softmax values across all images, used as IDF in the application.
- `.sumXY`: Contains sum of all outer products of softmax values across all images,
            can be used for covariance calculation.

`processing/create_index.py` script creates the inverted index for the UI application given
the `.annotation` file.

Formats of the files created for the UI application are described in the application's `README.md` file.

## Simulations
For user simulations `simulations/simulation.py` script is ready. Here are its options and some examples:

```
usage:
  --keyword KEYWORD     keyword vector filename
  --byte                convert keyword vectors to byte representation
  --idf IDF             unnormalized mean filename if IDF should be used
  --thresholds THRESHOLDS
                        ignore indexes with values smaller than threshold,
                        multiple thresholds divided by comma, default 'None'
                        for no threshold
  --similarity SIMILARITY
                        similarity vector filename if similarity reranking
                        should be used
  --disp_size DISP_SIZE
                        number of images which to choose the closest ones for
                        reranking from
  --n_closest N_CLOSEST
                        number of images to use for each reranking as a query
  --n_reranks N_RERANKS
                        number of similarity reranks to do for each image
  --filename FILENAME   common filename used for storing and restoring
                        samples, rankings and visualization
  --visualization VISUALIZATION
                        location of images if visualization should be used
  --restore_ranks       restore ranks from filename
  --gen_samples GEN_SAMPLES
                        number of samples to generate, if not used label_file
                        and log_file should be specified to load samples from
                        the user generated queries
  --query_lengths QUERY_LENGTHS
                        various lengths of queries to generate separated by
                        comma
  --label_file LABEL_FILE
                        standard label file
  --log_file LOG_FILE   log file of user generated queries
  --use_user_dist       generate samples from distribution given by user
                        queries
  --rank                perform ranking
  --graph               graph results
  --class_histogram     graph histogram of selected classes
```

#### Examples
Generate 100 queries of the network user with lengths 1,3 and up to 3 similarity reranks:
```
simulations/simulation.py --keyword=file.softmax --similarity=file.deep-features
                          --disp_size=50 --n_closest=1 --n_reranks=1,2,3
                          --filename=store_me_here --gen_samples=100 --query_lengths=1,3
                          --rank --graph
```
Show effect of threshold on real user keyword query without reranks:
```
simulations/simulation.py --keyword=file.softmax --filename=store_me_here
                          --thresholds=None,0.001,0.01 --label_file=file.label
                          --log_file=file.log --rank --graph
```

---

For further information go to the source files directly.
