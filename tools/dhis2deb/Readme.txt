Debian package of dhis2.  A bit raw round the edges. Tested on ubuntu 9.10.

To build a deb package:
1.  modify 1st line of Makefile (if necessary) to point at dhis.war to be packaged.
2.  Update version information in dhis2/DEBIAN/control
3.  type 'make clean' to cleanup up any old and temporary files
4.  type 'make update' to bring in dhis.war and update log4j.properties
5.  type 'make' to build deb package.

Thats it.  By default hibernate properties is setup to use h2 database in /opt/dhis2/database. This
can be changed to point to mysql, postgres or what have you.  

Tomcat should be running on http://localhost:8080. To manually restart Tomcat do:

sudo /etc/init.d/tomcat6 restart
Available options are:  start|stop|restart|try-restart|force-reload|status

Logging and other 'DHIS2_HOME' related stuff happens in /opt/dhis2.

Everything is owned by tomcat user and password files are chmof 600.

Two useful utility make targets are:
make uninstall - to uninstall the package
make install - to install the package.

Useful one-liner to do a complete install of latest build (probably should make this a make target):
'make uninstall; make clean; make update; make; make install'

The package depends on tomcat6. Install from package repository with 'apt-get install tomcat6'. You might need to do 'apt-get -f install' first to get dependent packages.

Apologies to the trendy for using 'make'.  Probably can do the same with maven but life is
too short :-)

Bob Jolliffe.

TODO:
More thoughtful upgrade/purge etc.  
Automatically handle version info.
