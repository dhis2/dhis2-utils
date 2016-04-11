package org.hisp.dhis.adhoc.command;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.amplecode.quick.BatchHandler;
import org.amplecode.quick.BatchHandlerFactory;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.dataelement.DataElement;
import org.hisp.dhis.dataelement.DataElementCategoryOptionCombo;
import org.hisp.dhis.dataelement.DataElementCategoryService;
import org.hisp.dhis.dataelement.DataElementService;
import org.hisp.dhis.datavalue.DataValue;
import org.hisp.dhis.datavalue.DataValueService;
import org.hisp.dhis.jdbc.batchhandler.DataValueBatchHandler;
import org.hisp.dhis.organisationunit.OrganisationUnit;
import org.hisp.dhis.organisationunit.OrganisationUnitService;
import org.hisp.dhis.period.Period;
import org.hisp.dhis.period.PeriodService;
import org.hisp.dhis.commons.collection.ListUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class RandomDataPopulator
{
    private static final Log log = LogFactory.getLog( RandomDataPopulator.class );
    
    private static final String DE_GROUP = "Svac1cNQhRS";
    private static final String DE_WEIGHT = "h0xKKjijTdI";
    private static final int OU_LEVEL = 4;
    private static final String PE_WEIGHT = "2016";
    private static final List<String> PERIODS = Arrays.asList( 
        "201501", "201502", "201503", "201504", "201505", "201506", "201507", "201508", "201509", "201510","201511", "201512", 
        "201601", "201602", "201603", "201604", "201605", "201606", "201607", "201608", "201609", "201610","201611", "201612"
    );
    
    @Autowired
    private DataElementService dataElementService;
        
    @Autowired
    private PeriodService periodService;
    
    @Autowired
    private DataElementCategoryService categoryService;
    
    @Autowired
    private BatchHandlerFactory batchHandlerFactory;
    
    @Autowired
    private OrganisationUnitService organisationUnitService;

    @Autowired
    private DataValueService dataValueService;
    
    @Transactional
    @Executed
    public void execute()
        throws Exception
    {
        // ---------------------------------------------------------------------
        // Data elements
        // ---------------------------------------------------------------------

        List<DataElement> des = new ArrayList<DataElement>( dataElementService.getDataElementGroup( DE_GROUP ).getMembers() );

        log.info( "Data elements: " + des.size() );
        
        // ---------------------------------------------------------------------
        // Organisation units
        // ---------------------------------------------------------------------

        List<OrganisationUnit> ous = new ArrayList<OrganisationUnit>( organisationUnitService.getOrganisationUnitsAtLevel( OU_LEVEL ) );
        Collections.shuffle( ous );
        ous = ListUtils.subList( ous, 0, 700 );
        
        log.info( "Organisation units: " + ous.size() );

        // ---------------------------------------------------------------------
        // Periods (might fail if not present in database due to single tx)
        // ---------------------------------------------------------------------

        List<Period> pes = periodService.reloadIsoPeriods( PERIODS );
        
        log.info( "Periods: " + pes );

        // ---------------------------------------------------------------------
        // Category option combos
        // ---------------------------------------------------------------------
        
        DataElementCategoryOptionCombo coc = categoryService.getDataElementCategoryOptionCombo( 1153734 );
        DataElementCategoryOptionCombo aoc = categoryService.getDefaultDataElementCategoryOptionCombo();

        // ---------------------------------------------------------------------
        // Weight data
        // ---------------------------------------------------------------------
        
        DataElement deWeight = dataElementService.getDataElement( DE_WEIGHT );
        Period peWeight = periodService.reloadIsoPeriod( PE_WEIGHT );
        
        Collection<DataValue> values = dataValueService.getDataValues( deWeight, peWeight, ous );
        
        Map<String, String> valueMap = new HashMap<String, String>();
        
        for ( DataValue value : values )
        {
            valueMap.put( value.getSource().getUid(), value.getValue() );
        }
        
        log.info( "Weight data values: " + valueMap.keySet().size() );
        
        // ---------------------------------------------------------------------
        // Setup and generation
        // ---------------------------------------------------------------------
        
        BatchHandler<DataValue> handler = batchHandlerFactory.createBatchHandler( DataValueBatchHandler.class ).init();

        Date d = new Date();
        
        int total = pes.size();
        int count = 0;

        Random r = new Random();
        
        for ( Period pe : pes )
        {
            double peFactor = ( ( r.nextInt( 50 ) + 75 ) / 100d );
            
            for ( OrganisationUnit ou : ous )
            {
                String val = valueMap.get( ou.getUid() );
            
                for ( DataElement de : des )
                {   
                    if ( val != null )
                    {
                        DataValue dv = new DataValue( de, pe, ou, coc, aoc, String.valueOf( getVal( val, peFactor ) ), "", d, "" );
                        handler.addObject( dv );
                    }
                }
            }
            
            log.info( "Done for " + ( ++count ) + " out of " + total );
        }
        
        handler.flush();
        
        log.info( "Data population completed" );
    }
    
    private Integer getVal( String value, double peFactor )
    {
        Random r = new Random();
        Double val = Double.parseDouble( value );
        Double delta = 30 * ( r.nextDouble() - 0.5 );
        Double weightedVal = ( val * 0.6 ) + delta;
        weightedVal = weightedVal * peFactor;
        return weightedVal.intValue();
    }    
}
