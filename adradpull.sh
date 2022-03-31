#!/bin/bash

while true
do
    if ping -c 1 adrad.geos.tamu.edu &> /dev/null
    then
        if [ ! -d adradDataIn/ ]
        then
            mkdir adradDataIn/
        fi
        rsync -uvcr --size-only --progress --protocol=30 -e "ssh -oKexAlgorithms=+diffie-hellman-group-exchange-sha1 -c aes128-cbc -i ~/.ssh/id_adrad" operator@adrad.geos.tamu.edu:/iris_data/product_raw/newest/. ./adradDataIn/
        sleep 2
        echo "Pull succeeded, waiting 15 seconds"
    else
        echo "ADRAD offline, waiting one minute"
        sleep 60
    fi
done
