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
import org.hisp.dhis.adhoc.Command;
import org.hisp.dhis.dataelement.DataElement;
import org.hisp.dhis.dataelement.DataElementCategoryOptionCombo;
import org.hisp.dhis.dataelement.DataElementCategoryService;
import org.hisp.dhis.dataelement.DataElementService;
import org.hisp.dhis.dataset.DataSetService;
import org.hisp.dhis.datavalue.DataValue;
import org.hisp.dhis.datavalue.DataValueService;
import org.hisp.dhis.jdbc.batchhandler.DataValueBatchHandler;
import org.hisp.dhis.organisationunit.OrganisationUnit;
import org.hisp.dhis.organisationunit.OrganisationUnitService;
import org.hisp.dhis.period.Period;
import org.hisp.dhis.period.PeriodService;
import org.hisp.dhis.system.util.ListUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class RandomDataPopulator
    implements Command
{
    private static final Log log = LogFactory.getLog( RandomDataPopulator.class );
    
    private static final String DE_GROUP = "Svac1cNQhRS";
    private static final String DE_WEIGHT = "h0xKKjijTdI";
    private static final int OU_LEVEL = 4;
    private static final String PE_WEIGHT = "2014";
    private static final List<String> PERIODS = Arrays.asList( 
        "201301", "201302", "201303", "201304", "201305", "201306", "201307", "201308", "201309", "201310","201311", "201312", 
        "201401", "201402", "201403", "201404", "201405", "201406", "201407", "201408", "201409", "201410","201411", "201412"
    );
    
    @Autowired
    private DataElementService dataElementService;
    
    @Autowired
    private DataSetService dataSetService;
    
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
    
    @Override
    @Transactional
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
        ous = ListUtils.subList( ous, 0, 4000 );
        
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
