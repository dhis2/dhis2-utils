package org.hisp.dhis.adhoc.command;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.dxf2.common.ImportOptions;
import org.hisp.dhis.dxf2.events.event.DataValue;
import org.hisp.dhis.dxf2.events.event.Event;
import org.hisp.dhis.dxf2.events.event.EventService;
import org.hisp.dhis.event.EventStatus;
import org.hisp.dhis.option.Option;
import org.hisp.dhis.option.OptionService;
import org.hisp.dhis.organisationunit.OrganisationUnit;
import org.hisp.dhis.organisationunit.OrganisationUnitService;
import org.hisp.dhis.program.ProgramService;
import org.hisp.dhis.system.util.DateUtils;
import org.hisp.dhis.util.Timer;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class RandomEventPopulator
{
    private static final Log log = LogFactory.getLog( RandomEventPopulator.class );
    
    private static final int EVENT_NO = 40000;
    private static final List<String> OPT_GENDER = Arrays.asList( "male", "female" );
    
    @Autowired
    private ProgramService programService;
    
    @Autowired
    private EventService eventService;
    
    @Autowired
    private OptionService optionService;
    
    @Autowired
    private OrganisationUnitService organisationUnitService;
    
    @Executed
    @Transactional
    public void execute()
    {
        List<Event> events = new ArrayList<Event>();
        
        List<Option> modeDischargeOptionSet = optionService.getOptionSet( "iDFPKpFTiVw" ).getOptions();
        List<Option> icd10OptionSet = optionService.getOptionSet( "eUZ79clX7y1" ).getOptions();
        List<OrganisationUnit> ous = new ArrayList<OrganisationUnit>( organisationUnitService.getOrganisationUnitsAtLevel( 4 ) );
        
        for ( int i = 0; i < EVENT_NO; i++ )
        {
            DateTime date = new DateTime( 2014, 1, 1, 12, 5 ).plusDays( new Random().nextInt( 363 ) );
            
            Event event = new Event();
            event.setStatus( EventStatus.COMPLETED );
            event.setProgram( "eBAyeGv0exc" ); // In-patient
            event.setProgramStage( "Zj7UnCAulEk" );
            event.setOrgUnit( ous.get( new Random().nextInt( ous.size() ) ).getUid() );
            event.setEventDate( DateUtils.getLongDateString( date.toDate() ) );            
            
            event.getDataValues().add( new DataValue( "qrur9Dvnyt5", String.valueOf( new Random().nextInt( 89 ) ) ) ); // Age
            event.getDataValues().add( new DataValue( "oZg33kd9taw", OPT_GENDER.get( new Random().nextInt( 2 ) ) ) ); // Gender
            event.getDataValues().add( new DataValue( "GieVkTxp4HH", String.valueOf( new Integer( 40 ) + new Random().nextInt( 150 ) ) ) ); // Height
            event.getDataValues().add( new DataValue( "vV9UWAZohSf", String.valueOf( new Integer( 15 ) + new Random().nextInt( 70 ) ) ) ); // Weight
            event.getDataValues().add( new DataValue( "eMyVanycQSC", DateUtils.getMediumDateString( new DateTime( date ).minusDays( 14 ).toDate() ) ) ); // Admission
            event.getDataValues().add( new DataValue( "msodh3rEMJa", DateUtils.getMediumDateString( new DateTime( date ).toDate() ) ) ); // Discharge
            event.getDataValues().add( new DataValue( "fWIAEtYVEGk", modeDischargeOptionSet.get( new Random().nextInt( 4 ) ).getCode() ) ); // Mode of discharge
            event.getDataValues().add( new DataValue( "K6uUAvq500H", icd10OptionSet.get( new Random().nextInt( 12000 ) ).getCode() ) ); // Diagnosis
            
            events.add( event );
        }

        log.info( "Populating events: " + events.size() );

        Timer t = new Timer().start();
                
        eventService.addEvents( events, new ImportOptions() );
        
        long s = t.getTimeInS();
        double a = EVENT_NO / s;
        
        log.info( "Event population done, seconds: " + s + ", event/s: " + a );
    }
}
