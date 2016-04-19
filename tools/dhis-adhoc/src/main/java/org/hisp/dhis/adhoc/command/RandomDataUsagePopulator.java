package org.hisp.dhis.adhoc.command;

import java.util.Random;

import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.datastatistics.DataStatistics;
import org.hisp.dhis.datastatistics.DataStatisticsService;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class RandomDataUsagePopulator
{
    @Autowired
    private DataStatisticsService dataStatisticsService;
    
    @Transactional
    @Executed
    public void execute()
        throws Exception
    {
        DateTime start = new DateTime( 2015, 1, 1, 0, 0 );
        DateTime end = new DateTime( 2016, 12, 31, 0, 0 );
        
        int w = 0;
        
        while ( start.isBefore( end ) )
        {
            if ( w % 3 == 0 )
            {
                w++;
            }
                        
            DataStatistics stats = new DataStatistics( rani( 110, 170 ), 
                ( rand( 410, 610 ) + w ), ( rand( 510, 710 ) + w ), ( rand( 410, 610 ) + w ), ( rand( 470, 630 ) + w ), 
                ( rand( 520, 610 ) + w ), ( rand( 620, 910 ) + w ), ( rand( 3200, 3400 ) + w ), 
                
                ( rand( 110, 150 ) + w ), ( rand( 120, 160 ) + w ), ( rand( 110, 150 ) + w ), ( rand( 130, 160 ) + w ), 
                ( rand( 110, 160 ) + w ), ( rand( 140, 180 ) + w ), ( rand( 140, 190 ) + w ),
                
                ( rani( 110, 150 ) + w ) );
            
            stats.setCreated( start.toDate() );
            
            dataStatisticsService.saveDataStatistics( stats );
            
            start = start.plusDays( 1 );
        }
    }
    
    private Double rand( int min, int max )
    {
        int r = new Random().nextInt( ( max - min ) );
        r += min;
        return (double) r;
    }

    private Integer rani( int min, int max )
    {
        int r = new Random().nextInt( ( max - min ) );
        r += min;
        return r;
    }

}
