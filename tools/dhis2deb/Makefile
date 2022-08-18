DHIS_WAR=~/src/dhis/dhis2-trunk/dhis2/dhis-2/dhis-web/dhis-web-portal/target/dhis.war

dhis2.deb: dhis2/* dhis2/dhis2_home/* dhis2/DEBIAN/*
	dpkg-deb --build dhis2

clean:
	rm -f dhis2/*~ dhis2/dhis2_home/*~ dhis2/DEBIAN/*~
	rm -f dhis2/*#* dhis2/dhis2_home/*#* dhis2/DEBIAN/*#*
	rm -f dhis2.deb

install: dhis2.deb
	sudo dpkg --install dhis2.deb 

uninstall: 
	sudo dpkg --remove dhis2 

update: 
	cp $(DHIS_WAR) dhis2/dhis.war
	cd dhis2; zip -f dhis.war ./WEB-INF/classes/log4j.properties
