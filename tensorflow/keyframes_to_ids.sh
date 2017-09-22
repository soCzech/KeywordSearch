# Takes TRECVid keyframes in subdirectories, moves them to one folder and updates names.

DIRECTORY=/mnt/c/Users/Tom/Desktop/Keyframes
NEW_DIRECTORY=/mnt/c/Users/Tom/Desktop/New_KF
VIDEO_BASELINE=35345

for subdir in $(ls ${DIRECTORY}); do
    for file in $(ls ${DIRECTORY}/${subdir}); do
        video_id=$(echo ${file} | sed -r 's/v([0-9]{5})_f([0-9]{5})_.*/\1/')
        video_id=$(expr ${video_id} - ${VIDEO_BASELINE})
        video_id=$(($video_id<<18))

        shot_id=$(echo ${file} | sed -r 's/v([0-9]{5})_f([0-9]{5})_.*/\2/')
        new_name=$(expr ${video_id} + ${shot_id}).jpg

        mv ${DIRECTORY}/${subdir}/${file} ${NEW_DIRECTORY}/${new_name}
        echo "${DIRECTORY}/${subdir}/${file} done"
    done
    rm -d ${DIRECTORY}/${subdir}
done