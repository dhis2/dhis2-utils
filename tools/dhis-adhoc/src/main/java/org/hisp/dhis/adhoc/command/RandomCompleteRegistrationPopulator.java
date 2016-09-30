package org.hisp.dhis.adhoc.command;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Map;

import org.hisp.quick.BatchHandler;
import org.hisp.quick.BatchHandlerFactory;
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

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;

public class RandomCompleteRegistrationPopulator
{
    private static final Log log = LogFactory.getLog( RandomCompleteRegistrationPopulator.class );

    private static final int OU_LEVEL = 4;
    
    private static final Map<String, Double> DATA_SETS = ImmutableMap.<String, Double>builder().
        put( "TuL8IOPzpHh", 0.85 ).put( "Rl58JxmKJo2", 0.85 ).put( "PLq9sJluXvc", 0.76 ).put( "EDzMBk0RRji", 0.94 ).
        build();
    
    private static final Map<String, Double> PERIODS = ImmutableMap.<String, Double>builder().
        put( "201501", 0.68 ).put( "201502", 0.71 ).put( "201503", 0.78 ).put( "201504", 0.72 ).
        put( "201505", 0.67 ).put( "201506", 0.82 ).put( "201507", 0.89 ).put( "201508", 0.92 ).
        put( "201509", 0.96 ).put( "201510", 0.92 ).put( "201511", 0.89 ).put( "201512", 0.99 ).
        put( "201601", 0.67 ).put( "201602", 0.69 ).put( "201603", 0.73 ).put( "201604", 0.79 ).
        put( "201605", 0.84 ).put( "201606", 0.89 ).put( "201607", 0.98 ).put( "201608", 0.96 ).
        put( "201609", 0.92 ).put( "201610", 0.80 ).put( "201611", 0.78 ).put( "201612", 0.83 ).build();
    
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
        List<DataSet> dss = idObjectManager.getObjects( DataSet.class, IdentifiableProperty.UID, DATA_SETS.keySet() );

        Date date = new Date();
        
        String storedBy = "admin";
        
        // ---------------------------------------------------------------------
        // Organisation units
        // ---------------------------------------------------------------------

        List<OrganisationUnit> ous = new ArrayList<OrganisationUnit>( organisationUnitService.getOrganisationUnitsAtLevel( OU_LEVEL ) );

        // ---------------------------------------------------------------------
        // Periods (might fail if not present in database due to single tx)
        // ---------------------------------------------------------------------

        List<Period> pes = periodService.reloadIsoPeriods( Lists.newArrayList( PERIODS.keySet() ) );
        
        log.info( "Periods: " + pes );

        BatchHandler<CompleteDataSetRegistration> batchHandler = batchHandlerFactory.createBatchHandler( CompleteDataSetRegistrationBatchHandler.class ).init();

        for ( DataSet ds : dss )
        {
            for ( DataElementCategoryOptionCombo aoc : ds.getCategoryCombo().getOptionCombos() )
            {
                for ( Period pe : pes )
                {
                    Double weight = DATA_SETS.get( ds.getUid() ) * PERIODS.get( pe.getIsoDate() );
                    
                    Double ouMax = ous.size() * weight;
                    
                    log.info( "Org unit max: " + ouMax );
                                        
                    Collections.shuffle( ous );
                    List<OrganisationUnit> subOus = ListUtils.subList( ous, 0, ouMax.intValue() );
                    
                    for ( OrganisationUnit ou : subOus )
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
