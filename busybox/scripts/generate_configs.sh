#!/bin/bash

DB_FILE=.db
CONFIG=.config
OUT_DIR=randconfig_generated
NB_CONFIGS=$1

touch $DB_FILE
mkdir -p $OUT_DIR

i=1
while [[ $i -le $NB_CONFIGS ]] ;
do
    make randconfig >> /dev/null 2>&1
    CKSUM=$(sed '4d' $CONFIG | cksum)
    if [[ ! $(grep "$CKSUM" $DB_FILE) ]] ; then
        echo "$CKSUM" >> $DB_FILE
        ii=$(printf "%04d" $i)
        mv $CONFIG $OUT_DIR/${ii}_randconfig
        i=$[$i+1]
    fi
done

rm $DB_FILE
