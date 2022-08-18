#!/bin/bash

# first fixing up the horrible mess bazzar makes of file permissions
find ./pkg -type d -exec chmod 0755 {} \;
find ./pkg -type f -exec chmod 0644 {} \;

chmod 0755 pkg/usr/bin/*
chmod 0700 pkg/usr/share/dhis2-tools/skel/backups/ 
chmod 0644 pkg/DEBIAN/conffiles 
chmod 0755 pkg/DEBIAN/postinst
chmod 0755 pkg/DEBIAN/preinst 
chmod 0755 pkg/DEBIAN/postrm 
chmod 0440 pkg/etc/sudoers.d/dhis2
chmod 0755 pkg/usr/share/dhis2-tools/skel/bin/setenv.sh

# clean up any trash backup files
cd ./pkg
find . -iname  *~ -exec rm '{}' ';'

# generate the md5sums
find . -type f ! -regex '.*.hg.*' ! -regex '.*?debian-binary.*' ! -regex '.*?DEBIAN.*' -printf '%P ' | xargs md5sum > DEBIAN/md5sums
chmod 644 DEBIAN/md5sums
cd ..

# assemble the deb package
fakeroot dpkg -b ./pkg $1
