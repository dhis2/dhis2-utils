#!/usr/bin/env bash
#       ____  __  ______________ 
#      / __ \/ / / /  _/ ___/__ \
#     / / / / /_/ // / \__ \__/ /
#    / /_/ / __  // / ___/ / __/ 
#   /_____/_/ /_/___//____/____/
#
#   DHIS2 installation helper script

set -e

# Make sure we are on a supported distribution
DISTRO=$(lsb_release -si)
RELEASE=$(lsb_release -sr)
 
echo "Attempting installion of dhis2-tools on $DISTRO linux version $RELEASE"
# No CentOS version yet :-(
if [ $DISTRO != 'Ubuntu' ]
then
  echo "Sorry installation only supported on Ubuntu at this time"
  echo "Exiting ..."
  exit 1
fi

# Only tested on LTS Ubuntu versions
case $RELEASE in

  12.04)
    echo "installing on 12.04"
    echo "setup repositories for postgresql and nginx";
    # new way to install postgres 9.2 (https://wiki.postgresql.org/wiki/Apt)
    echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -sc)-pgdg main" >/etc/apt/sources.list.d/pgdg.list
    wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -
    # need to use a ppa for nginx
    apt-get -y install python-software-properties -y
    add-apt-repository ppa:nginx/stable -y;; 

  14.04)
    echo "installing on 14.04";;

  *)
    echo "Only Ubuntu LTS releases (12.04 and 14.04) are supported";
    echo "Exiting ...";
    exit 1;;
esac

# add dhis2 apt repository to sources
echo 'deb http://apt.dhis2.org/amd64 /' > /etc/apt/sources.list.d/dhis2.list 
wget -O - http://apt.dhis2.org/keyFile |apt-key add -

apt-get update -y

# install the dhis2-tools deb
apt-get install dhis2-tools 

# Uncomment below to install postgres and nginx servers on this machine
# apt-get -y install nginx postgresql 
echo "The dhis2-tools are now installed. You may also want to"
echo "install nginx and postgresql servers on this machine. You"
echo "can do so by running:"
echo
echo "apt-get install nginx postgresql"
echo
echo "Type 'apropos dhis2' to see available manual pages."
