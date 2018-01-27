TRANSCRIPT="http://www-nlpir.nist.gov/projects/tv2016/pastdata/iacc.3.asr/asr.tgz"
SHOT_REF="http://www-nlpir.nist.gov/projects/tv2016/pastdata/iacc.3.master.shot.reference/iacc.3.collection.xml"

if [ ${#} -ne 1 ]; then
    echo "Illegal number of arguments"
    echo "    1: DIRECTORY where to store the transcript"
    exit
fi

DIRECTORY="${1}"

if [ ! -d "${DIRECTORY}" ]; then
  mkdir -p "${DIRECTORY}"
  echo "Directory ${DIRECTORY} created."
fi
cd "${DIRECTORY}"

echo "Downloading transcript."
wget --no-verbose -c ${SHOT_REF}
wget --no-verbose -c ${TRANSCRIPT}

echo "Unpacking transcript."
tar -xzf asr.tgz

rm asr.tgz

echo "Run parse_audio_transcript.py with parameters:"
echo "    -vf path_to/video_folder/"
echo "    -mf path_to/iacc.3.collection.xml"
echo "    -lf path_to/transcript.label"
echo "    -pf path_to/transcript.pseudo-index"
