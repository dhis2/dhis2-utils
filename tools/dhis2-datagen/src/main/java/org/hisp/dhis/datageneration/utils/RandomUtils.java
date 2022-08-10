package org.hisp.dhis.datageneration.utils;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.Point;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static net.andreinc.mockneat.unit.time.LocalDates.localDates;

public class RandomUtils
{
    public static Point createRandomPoint()
    {
        double latitude = (Math.random() * 180.0) - 90.0;
        double longitude = (Math.random() * 360.0) - 180.0;
        GeometryFactory geometryFactory = new GeometryFactory();
        /* Longitude (= x coord) first ! */
        return geometryFactory.createPoint( new Coordinate( longitude, latitude ) );
    }

    public static String localDateTime()
    {
        return localDates().thisYear().display( DateTimeFormatter.ISO_LOCAL_DATE ).get() + " 00:00:00";
    }

    public static String localDateTimeInFuture()
    {
        LocalDateTime localDateTime = new Date().toInstant().atZone( ZoneId.systemDefault() ).toLocalDateTime();
        return localDates().future( localDateTime.plusYears( 1 ).toLocalDate() )
            .display( DateTimeFormatter.ISO_LOCAL_DATE ).get() + " 00:00:00";
    }

    public static List<Integer> randomizeSequence( int collectionSize )
    {
        List<Integer> indexes = new ArrayList<>();
        if ( collectionSize == 1 )
        {
            indexes.add( 0 );
        }
        else
        {
            indexes = IntStream.range( 0, collectionSize - 1 ).boxed()
                .collect( Collectors.toCollection( ArrayList::new ) );
            Collections.shuffle( indexes );
            indexes = indexes.subList( 0, (collectionSize > indexes.size() ? indexes.size() - 1 : collectionSize) );
        }
        return indexes;
    }
}
