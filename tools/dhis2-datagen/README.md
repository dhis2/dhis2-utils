# DHIS2 DATAGEN

A command line tool to generate large amount of data for performance test of the DHIS2 application.
This application generates a file containing INSERT statements that can be imported into the database.

## Requirements

    Java 8
    Postgres

## Build

    mvn clean install
    
## Configuration

Datagen uses the same configuration file used by DHIS2 for connecting to the database.
Upon starting, the application builds a cache of common entities (such as Programs). The cache is populated
by accessing the database configured in the standard dhis2 configuration file.
    
## Run

    java -jar target/datagen-0.0.1-SNAPSHOT.jar
    
## Command line options

- `help` shows a contextual help
- `gen` generates the INSERT file

### `gen` options

- `-S` `--size` number of entities to generate
- `-T` `--type` type of entities to generate (currently only the option `TEI` is supported)
- `-F` `--file` location of the target file

### Optional `gen` options

- `--events` range of events to generate for each TEI (format XX-XX, e.g. 1-10) 
- `--attributes` range of attributes values to generate for each TEI (format XX-XX, e.g. 1-10)
- `--dataValues` range of data values to generate for each TEI (format XX-XX, e.g. 1-10)

Example:

`gen -S 100000 -T TEI -F /home/dhis2/10K.sql --events 1-5 --attributes 10-20 --dataValues 1-10`

The above command will generate a file containing the INSERT statements for ten thousands TEI. Each TEI \
will have a random number of events between 1 and 5, a random number of attribute values between 10 and 20 and
a random number of Data Values between 1 and 10.

## Open points

When starting a generation process, the application gets the first available primary key from all the tables
that are involved in the generation and increment each id for each generated row.
After the file is generated and imported into the database, the application sequences are out of sync.