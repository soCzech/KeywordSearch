labels="classes.labels"

if [ ! -f $labels ]
then
	echo "File $labels does not exist. Generate it first."
    exit 1
fi

cut -f2 -d'~' $labels > synset_ids.txt

#nohup ./script.sh < input_file &
#ps -eaf

directory='synsets'

if [ ! -d "$directory" ]; then
	mkdir "$directory"
fi

while read synset_id; do
	echo "Processing $synset_id"
	size=$(curl --head "http://www.image-net.org/download/synset?wnid=$synset_id&username=tomassoucek&accesskey=a1ea3e2d98d50626018471393a1cda9b58f2aaed&release=latest&src=stanford" 2>/dev/null | egrep 'Content-Length:' | sed -e 's/Content-Length: //')
	echo "Size: $size"
	echo "Downloading..."
	# --no-verbose
	wget --no-verbose -c -O "$directory/$synset_id.tar" "http://www.image-net.org/download/synset?wnid=$synset_id&username=tomassoucek&accesskey=a1ea3e2d98d50626018471393a1cda9b58f2aaed&release=latest&src=stanford"	
	
	if [ ! -d "$directory/$synset_id" ]; then
		mkdir "$directory/$synset_id"
	fi
	tar -xf "$directory/$synset_id.tar" -C "$directory/$synset_id"
	
	ls "$directory/$synset_id/*.JPEG" | tail -n +1000 | xargs -d '\n' rm --
	mogrify -resize "320x320>" "$directory/$synset_id/*.JPEG"
done < synset_ids.txt
