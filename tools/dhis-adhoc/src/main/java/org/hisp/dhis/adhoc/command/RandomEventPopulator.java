package org.hisp.dhis.adhoc.command;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

import org.hisp.dhis.adhoc.Command;
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
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class RandomEventPopulator
    implements Command
{
    private static final int EVENT_NO = 10000;
    private static final List<String> OPT_GENDER = Arrays.asList( "male", "female" );
    
    @Autowired
    private ProgramService programService;
    
    @Autowired
    private EventService eventService;
    
    @Autowired
    private OptionService optionService;
    
    @Autowired
    private OrganisationUnitService organisationUnitService;
        
    @Override
    @Transactional
    public void execute()
        throws Exception
    {
        List<Event> events = new ArrayList<Event>();
        
        List<Option> modeDischargeOptionSet = optionService.getOptionSet( "iDFPKpFTiVw" ).getOptions();
        List<Option> icd10OptionSet = optionService.getOptionSet( "eUZ79clX7y1" ).getOptions();
        List<OrganisationUnit> ous = new ArrayList<OrganisationUnit>( organisationUnitService.getOrganisationUnitsAtLevel( 4 ) );
        
        for ( int i = 0; i < EVENT_NO; i++ )
        {
            DateTime date = new DateTime( 2015, 1, 1, 12, 5 ).plusDays( new Random().nextInt( 363 ) );
            
            Event event = new Event();
            event.setStatus( EventStatus.COMPLETED );
            event.setProgram( "eBAyeGv0exc" ); // In-patient
            event.setProgramStage( "Zj7UnCAulEk" );
            event.setOrgUnit( ous.get( new Random().nextInt( ous.size() ) ).getUid() );
            event.setEventDate( DateUtils.getLongDateString( date.toDate() ) );            
            
            event.getDataValues().add( new DataValue( "qrur9Dvnyt5", String.valueOf( new Random().nextInt( 89 ) ) ) );
            event.getDataValues().add( new DataValue( "oZg33kd9taw", OPT_GENDER.get( new Random().nextInt( 2 ) ) ) );
            event.getDataValues().add( new DataValue( "eMyVanycQSC", DateUtils.getMediumDateString( new DateTime( date ).minusDays( 14 ).toDate() ) ) );
            event.getDataValues().add( new DataValue( "msodh3rEMJa", DateUtils.getMediumDateString( new DateTime( date ).toDate() ) ) );
            event.getDataValues().add( new DataValue( "fWIAEtYVEGk", modeDischargeOptionSet.get( new Random().nextInt( 4 ) ).getCode() ) );
            event.getDataValues().add( new DataValue( "K6uUAvq500H", icd10OptionSet.get( new Random().nextInt( 12000 ) ).getCode() ) );
            
            events.add( event );
        }
        
        eventService.addEvents( events, new ImportOptions() );
    }
}
