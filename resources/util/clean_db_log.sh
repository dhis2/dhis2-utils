#!/bin/sh

# Removes analytics table stuff from log files

# First argument is name of log file

sed -i 's/insert into analytics//g' $1
sed -i 's/create index//g' $1
