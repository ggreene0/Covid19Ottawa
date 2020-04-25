#/bin/bash

./update.py

if [ $? == 0 ]
then
    DATE_STRING=$(date -r timeseries/ottawa_cases.csv "+%Y-%m-%d %H:%M %Z")
    echo ${DATE_STRING} > update_time.txt
    COMMIT_MSG="Update data: ${DATE_STRING}"

    git add timeseries/ottawa_cases.csv
    git add update_time.txt
    git commit -m "${COMMIT_MSG}"
    git push
fi
