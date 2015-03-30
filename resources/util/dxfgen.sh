#!/bin/bash
# WIP script to generate schema from annotated classes
# Currently a bit flaky cos of having to manually set the classpath.
# Will be better to run as a maven target.

# adjust this
DHIS_API=~/src/dhis/dhis2-dxf2/dhis-2/dhis-api

# the files which have xml annotations formatted as a simple list of files
# separated by space
FILES=$(grep -rl '@XmlRootElement' --include=*.java $DHIS_API |awk '{printf "%s ",$0 }' -)

# maven would sure make this easier :-(
CLASSPATH+='~/.m2/repository/org/codehaus/jackson/jackson-core-asl/1.9.2/jackson-core-asl-1.9.2.jar:'
CLASSPATH+='~/.m2/repository/org/codehaus/jackson/jackson-mapper-asl/1.9.2/jackson-mapper-asl-1.9.2.jar:'
CLASSPATH+='~/.m2/repository/org/hisp/dhis/dhis-api/2.6-SNAPSHOT/dhis-api-2.6-SNAPSHOT.jar:'
CLASSPATH+='/home/bobj/.m2/repository/org/codehaus/jackson/jackson-xc/1.9.2/jackson-xc-1.9.2.jar:'
CLASSPATH+='/home/bobj/.m2/repository/commons-lang/commons-lang/2.6/commons-lang-2.6.jar'

# for some reason this is not working for me.  So I have to manually set the classpath in the 
# bash shell.  That's why I echo it out for now.  Something stupid here.
export CLASSPATH
echo set CLASSPATH to: $CLASSPATH

schemagen -d $DHIS_API/target -cp $CLASSPATH $FILES 

echo
echo 'Schemagen is telling you lies :-)'
echo Schema file is generated in $DHIS_API/target

