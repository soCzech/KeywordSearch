# nohup ./script.sh &

if [ ${#} -ne 3 ]; then
    echo "Illegal number of arguments"
    echo "    1: DIRECTORY where to store images"
    echo "    2: USERNAME for ImageNet download"
    echo "    3: ACCESS_KEY for ImageNet download"
    exit
fi

DIRECTORY="${1}"
USERNAME="${2}"
ACCESS_KEY="${3}"

if [ ! -d "${DIRECTORY}" ]; then
  mkdir -p "${DIRECTORY}"
  echo "Directory ${DIRECTORY} created."
fi
cd "${DIRECTORY}"



### LABELS ###
mkdir -p "labels"
cd "labels"

echo "Downloading class names from ImageNet"
wget --no-verbose http://www.image-net.org/api/xml/ReleaseStatus.xml
# wget --no-verbose http://www.image-net.org/api/xml/structure_released.xml

echo "Selecting classes with over 1000 images"
egrep 'winter11" numImages="([1,2][0-9]{3})"' ReleaseStatus.xml | sed -e 's/.*"\(n.*\)" re.*/\1/' | sort > ids_over_1000.txt

# echo "Generaring glossary"
# sed 's/^[^"]*"\([^"]*\)"[^"]*"\([^"]*\)"[^"]*"\([^"]*\)".*/\1~\2~\3/' structure_released.xml | sed '/^[^n]/d' | sort | uniq > glossary.txt
# echo "Generaring labels"
# join -t'~' glossary.txt ids_over_1000.txt | nl -nln -s'~' -w1 -v0 > labels.txt
# 8 labels missing in gloss

cd ..



### DOWNLOAD SYNSETS ###
mkdir -p "synsets.tar"

echo "Downloading images from ImageNet"
while read synset_id
do
    url="http://www.image-net.org/download/synset?wnid=${synset_id}&username=${USERNAME}&accesskey=${ACCESS_KEY}&release=latest&src=stanford"
	wget --no-verbose -c -O synsets.tar/${synset_id}.tar ${url}
done < labels/ids_over_1000.txt



### UNPACK SYNSETS ###
echo "Unpacking images from ImageNet"

while read synset_id
do
	if [ ! -f synsets.tar/${synset_id}.tar ]; then
		echo "Skipping ${synset_id}."
		continue
	fi

	echo "Processing ${synset_id}."
	mkdir -p synsets.unpacked/${synset_id}

	tar -xf synsets.tar/${synset_id}.tar -C synsets.unpacked/${synset_id}

	ls synsets.unpacked/${synset_id}/*.JPEG | tail -n +1001 | xargs -d '\n' rm --
	mogrify -resize "400^" synsets.unpacked/${synset_id}/*.JPEG

done < labels/ids_over_1000.txt
