mkdir labels
cd labels
echo "Downloading class names from ImageNet"
wget http://www.image-net.org/api/xml/ReleaseStatus.xml
wget http://www.image-net.org/api/xml/structure_released.xml
echo "Selecting classes with over 1000 images"
egrep 'winter11" numImages="([1,2][0-9]{3})"' ReleaseStatus.xml | sed -e 's/.*"\(n.*\)" re.*/\1/' | sort > ids_over_1000.txt
echo "Generaring glossary"
sed 's/^[^"]*"\([^"]*\)"[^"]*"\([^"]*\)"[^"]*"\([^"]*\)".*/\1~\2~\3/' structure_released.xml | sed '/^[^n]/d' | sort | uniq > glossary.txt
echo "Generaring labels"
join -t'~' glossary.txt ids_over_1000.txt | nl -nln -s'~' -w1 -v0 > ../classes.labels # 8 labels missing in gloss