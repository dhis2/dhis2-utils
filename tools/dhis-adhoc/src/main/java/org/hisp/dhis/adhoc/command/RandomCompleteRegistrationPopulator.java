package org.hisp.dhis.adhoc.command;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.List;

import org.amplecode.quick.BatchHandler;
import org.amplecode.quick.BatchHandlerFactory;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.common.IdentifiableObjectManager;
import org.hisp.dhis.common.IdentifiableProperty;
import org.hisp.dhis.commons.collection.ListUtils;
import org.hisp.dhis.dataelement.DataElementCategoryOptionCombo;
import org.hisp.dhis.dataset.CompleteDataSetRegistration;
import org.hisp.dhis.dataset.DataSet;
import org.hisp.dhis.jdbc.batchhandler.CompleteDataSetRegistrationBatchHandler;
import org.hisp.dhis.organisationunit.OrganisationUnit;
import org.hisp.dhis.organisationunit.OrganisationUnitService;
import org.hisp.dhis.period.Period;
import org.hisp.dhis.period.PeriodService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class RandomCompleteRegistrationPopulator
{
    private static final Log log = LogFactory.getLog( RandomCompleteRegistrationPopulator.class );

    private static final int OU_LEVEL = 4;
    
    private static final List<String> DATA_SETS = Arrays.asList( 
        "Rl58JxmKJo2", "PLq9sJluXvc", "EDzMBk0RRji", "V8MHeZHIrcP", "VTdjfLXXmoi" );
    
    private static final List<String> PERIODS = Arrays.asList( 
        "201501", "201502", "201503", "201504", "201505", "201506", "201507", "201508", "201509", "201510","201511", "201512", 
        "201601", "201602", "201603", "201604", "201605", "201606", "201607", "201608", "201609", "201610","201611", "201612"
    );
    
    @Autowired
    private IdentifiableObjectManager idObjectManager;

    @Autowired
    private PeriodService periodService;
    
    @Autowired
    private BatchHandlerFactory batchHandlerFactory;

    @Autowired
    private OrganisationUnitService organisationUnitService;

    @Transactional
    @Executed
    public void execute()
        throws Exception
    {
        List<DataSet> dss = idObjectManager.getObjects( DataSet.class, IdentifiableProperty.UID, DATA_SETS );

        Date date = new Date();
        
        String storedBy = "admin";
        
        // ---------------------------------------------------------------------
        // Organisation units
        // ---------------------------------------------------------------------

        List<OrganisationUnit> ous = new ArrayList<OrganisationUnit>( organisationUnitService.getOrganisationUnitsAtLevel( OU_LEVEL ) );

        // ---------------------------------------------------------------------
        // Periods (might fail if not present in database due to single tx)
        // ---------------------------------------------------------------------

        List<Period> pes = periodService.reloadIsoPeriods( PERIODS );
        
        log.info( "Periods: " + pes );

        BatchHandler<CompleteDataSetRegistration> batchHandler = batchHandlerFactory.createBatchHandler( CompleteDataSetRegistrationBatchHandler.class ).init();

        for ( DataSet ds : dss )
        {
            for ( Period pe : pes )
            {
                Collections.shuffle( ous );
                List<OrganisationUnit> subOus = ListUtils.subList( ous, 0, 650 );
                
                for ( OrganisationUnit ou : subOus )
                {
                    for ( DataElementCategoryOptionCombo aoc : ds.getCategoryCombo().getOptionCombos() )
                    {
                        CompleteDataSetRegistration cdr = new CompleteDataSetRegistration( ds, pe, ou, aoc, date, storedBy );
                        
                        batchHandler.addObject( cdr );
                    }                
                }
            }
            
            log.info( "Done for data set: " + ds );
        }
        
        batchHandler.flush();
        
        log.info( "Registration population completed" );
    }
}
