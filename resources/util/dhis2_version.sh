#!/usr/bin/env bash

# unpick and dump the build properties from a dhis2 war file
# Bob Jolliffe 2012-01-31 v1

if [[ "$#" != 1 ]]; then 
  echo "usage:  $0 <dhis-war-file>"
  exit 1
fi

test -e $1 || {
  echo "error: $1 doesn't exist!"
  exit 1
}

test -r $1 || {
  echo "error: $1 is not readable!"
  exit 1
}
 

COMMONS_JAR=$(mktemp)

unzip -pqq $1 WEB-INF/lib/dhis-web-commons* > $COMMONS_JAR

#TODO - test zero length
test -s $COMMONS_JAR || { 
  echo "Couldn't find dhis-web-commons-*.jar"
  echo "Could be $1 is not a valid dhis war file?"     
  rm $COMMONS_JAR
  exit 1
}

BUILD_PROPS=$(unzip -p $COMMONS_JAR build.properties)

# TODO - unpick these properties
# for now just dump them ...
echo $BUILD_PROPS

# cleanup
rm $COMMONS_JAR
exit 0
