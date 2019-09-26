package org.hisp.dhis.datageneration.utils;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.Point;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Date;

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

}
