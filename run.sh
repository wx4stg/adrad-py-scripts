#!/bin/bash
source config.txt
while true
do
    if ping -c 1 adrad.geos.tamu.edu &> /dev/null
    then
        if [ ! -d adradDataIn/ ]
        then
            mkdir adradDataIn/
        fi
        rsync -uvcr --size-only --progress --protocol=30 -e "ssh -oKexAlgorithms=+diffie-hellman-group-exchange-sha1 -c aes128-cbc -i ~/.ssh/id_adrad" operator@adrad.geos.tamu.edu:/iris_data/product_raw/newest/. ./input-realtime/
        $pathToPy processRealtime.py $realtimeOutputPath
        sleep 10
        echo "Pull succeeded, waiting 10 seconds"
    else
        echo "ADRAD offline, waiting one minute"
        $pathToPy processArchive.py $archiveOutputPath
        sleep 60
    fi
done
