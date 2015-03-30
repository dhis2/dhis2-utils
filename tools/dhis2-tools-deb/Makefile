TARGET=dhis2-tools_1.1-0ubuntu1_all.deb

all: deb test

deb: doc
	./assemble.sh $(TARGET)

doc:
	cd docs; make; cd ..

test: 
	lintian $(TARGET)

clean:
	rm -f $(TARGET)
	rm -rf *~
	cd docs; make clean; cd ..
