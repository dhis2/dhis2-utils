package org.hisp.dhis.adhoc.command;

import static java.nio.charset.StandardCharsets.UTF_8;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.dataelement.DataElement;
import org.hisp.dhis.dataelement.DataElementService;
import org.hisp.dhis.option.OptionService;
import org.hisp.dhis.option.OptionSet;
import org.hisp.dhis.organisationunit.OrganisationUnit;
import org.hisp.dhis.organisationunit.OrganisationUnitService;
import org.hisp.dhis.program.Program;
import org.hisp.dhis.program.ProgramInstance;
import org.hisp.dhis.program.ProgramInstanceService;
import org.hisp.dhis.program.ProgramService;
import org.hisp.dhis.program.ProgramStage;
import org.hisp.dhis.program.ProgramStageInstance;
import org.hisp.dhis.program.ProgramStageInstanceService;
import org.hisp.dhis.program.ProgramStageService;
import org.hisp.dhis.trackedentity.TrackedEntity;
import org.hisp.dhis.trackedentity.TrackedEntityAttribute;
import org.hisp.dhis.trackedentity.TrackedEntityAttributeService;
import org.hisp.dhis.trackedentity.TrackedEntityInstance;
import org.hisp.dhis.trackedentity.TrackedEntityInstanceService;
import org.hisp.dhis.trackedentity.TrackedEntityService;
import org.hisp.dhis.trackedentityattributevalue.TrackedEntityAttributeValue;
import org.hisp.dhis.trackedentityattributevalue.TrackedEntityAttributeValueService;
import org.hisp.dhis.trackedentitydatavalue.TrackedEntityDataValue;
import org.hisp.dhis.trackedentitydatavalue.TrackedEntityDataValueService;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.transaction.annotation.Transactional;

import com.csvreader.CsvReader;

public class RandomChildrenPopulator
{
    private static final Log log = LogFactory.getLog( RandomChildrenPopulator.class );
    
    @Autowired
    private TrackedEntityInstanceService teiService;
    
    @Autowired
    private TrackedEntityService teService;
    
    @Autowired
    private ProgramService programService;
    
    @Autowired
    private ProgramStageService programStageService;
    
    @Autowired
    private ProgramInstanceService programInstanceService;
    
    @Autowired
    private ProgramStageInstanceService psiService;

    @Autowired
    private TrackedEntityAttributeService attributeService;

    @Autowired
    private TrackedEntityAttributeValueService attributeValueService;
    
    @Autowired
    private TrackedEntityDataValueService dataValueService;
    
    @Autowired
    private DataElementService dataElementService;
    
    @Autowired
    private OptionService optionService;
    
    @Autowired
    private OrganisationUnitService organisationUnitService;

    @Executed
    @Transactional
    public void execute()
        throws Exception
    {
        TrackedEntity person = teService.getTrackedEntity( "cyl5vuJ5ETQ" );
        
        Program pr = programService.getProgram( "IpHINAT79UW" );
        ProgramStage ps1 = programStageService.getProgramStage( "A03MvHHogjR" );
        ProgramStage ps2 = programStageService.getProgramStage( "ZzYYXq4fJie" );
        
        List<OrganisationUnit> ous = new ArrayList<OrganisationUnit>( organisationUnitService.getOrganisationUnitsAtLevel( 4 ) );
        
        TrackedEntityAttribute atFirstName = attributeService.getTrackedEntityAttribute( "dv3nChNSIxy" );
        TrackedEntityAttribute atLastName = attributeService.getTrackedEntityAttribute( "hwlRTFIFSUq" );
        TrackedEntityAttribute atGender = attributeService.getTrackedEntityAttribute( "cejWyOfXge6" );
        
        // Stage 1
        DataElement deApgar = dataElementService.getDataElement( "a3kGcGDCuk6" );
        DataElement deWeight = dataElementService.getDataElement( "UXz7xuGCEhU" );
        DataElement deArv = dataElementService.getDataElement( "wQLfBvPrXqq" );
        OptionSet osArv = optionService.getOptionSet( "f38bstJioPs" );
        DataElement deBcg = dataElementService.getDataElement( "bx6fsa0t90x" );
        DataElement deOpv = dataElementService.getDataElement( "ebaJjqltK5N" );
        OptionSet osOpv = optionService.getOptionSet( "kzgQRhOCadd" );
        DataElement deInfFeed = dataElementService.getDataElement( "X8zyunlgUfM" );
        OptionSet osInfFeed = optionService.getOptionSet( "x31y45jvIQL" );
        
        // Stage 2
        DataElement deInfWeight = dataElementService.getDataElement( "GQY2lXrypjO" );
        DataElement deMeasles = dataElementService.getDataElement( "FqlgKAG8HOu" );
        DataElement dePenta = dataElementService.getDataElement( "vTUhAUZFoys" );
        OptionSet osPenta = optionService.getOptionSet( "kzgQRhOCadd" );
        DataElement deYelFev = dataElementService.getDataElement( "rxBfISxXS2U" );
        DataElement deIpt = dataElementService.getDataElement( "lNNb3truQoi" );
        OptionSet osIpt = optionService.getOptionSet( "nH8Y04zS7UV" );
        DataElement deDpt = dataElementService.getDataElement( "pOe0ogW4OWd" );
        OptionSet osDpt = optionService.getOptionSet( "udkr3ihaeD3" );
        DataElement deVitA = dataElementService.getDataElement( "HLmTEmupdX0" );
        DataElement deHivRes = dataElementService.getDataElement( "cYGaxwK615G" );
        OptionSet osHivRes = optionService.getOptionSet( "oXR37f2wOb1" );
        DataElement deHivTest = dataElementService.getDataElement( "hDZbpskhqDd" );
        OptionSet osHivTest = optionService.getOptionSet( "OGmE3wUMEzu" );
        DataElement deChildArv = dataElementService.getDataElement( "sj3j9Hwc7so" );
        OptionSet osChildArv = optionService.getOptionSet( "dgsftM0rXu2" );
        
        CsvReader reader = new CsvReader( new ClassPathResource( "sample_children.csv" ).getInputStream(), UTF_8 );
        reader.readHeaders();
        
        int c = 0;
        
        while ( reader.readRecord() )
        {
            DateTime date = new DateTime( 2015, 1, 1, 12, 5 ).plusDays( new Random().nextInt( 363 ) );
            DateTime date2 = date.plusDays( 21 );
            
            OrganisationUnit ou = ous.get( new Random().nextInt( ous.size() ) );
            
            // first_name, last_name, gender
            
            String[] values = reader.getValues();
            
            TrackedEntityInstance tei = new TrackedEntityInstance();
            
            tei.setOrganisationUnit( ou );
            tei.setTrackedEntity( person );
            
            teiService.addTrackedEntityInstance( tei );
            
            Set<TrackedEntityAttributeValue> attributeValues = new HashSet<>();

            attributeValues.add( new TrackedEntityAttributeValue( atFirstName, tei, values[0] ) );
            attributeValues.add( new TrackedEntityAttributeValue( atLastName, tei, values[1] ) );
            attributeValues.add( new TrackedEntityAttributeValue( atGender, tei, values[2] ) );
            
            for ( TrackedEntityAttributeValue attributeValue : attributeValues )
            {
                attributeValueService.addTrackedEntityAttributeValue( attributeValue );
            }
            
            ProgramInstance pi = programInstanceService.enrollTrackedEntityInstance( tei, pr, date.toDate(), date.toDate(), ou );
            
            ProgramStageInstance psi1 = new ProgramStageInstance( pi, ps1 );
            psi1.setDueDate( date.toDate() );
            psi1.setExecutionDate( date.toDate() );
            psi1.setOrganisationUnit( ou );
            
            psiService.addProgramStageInstance( psi1 );
            
            ProgramStageInstance psi2 = new ProgramStageInstance( pi, ps2 );
            psi2.setDueDate( date2.toDate() );
            psi2.setExecutionDate( date2.toDate() );
            psi2.setOrganisationUnit( ou );

            psiService.addProgramStageInstance( psi2 );
            
            List<TrackedEntityDataValue> dvs = new ArrayList<>();       

            dvs.add( new TrackedEntityDataValue( psi1, deApgar, date.toDate(), String.valueOf( new Random().nextInt( 3 ) ) ) );
            dvs.add( new TrackedEntityDataValue( psi1, deWeight, date.toDate(), String.valueOf( ( 2500 + new Random().nextInt( 1500 ) ) ) ) );
            dvs.add( new TrackedEntityDataValue( psi1, deArv, date.toDate(), getRandomOptionSetCode( osArv  ) ) );
            dvs.add( new TrackedEntityDataValue( psi1, deBcg, date.toDate(), getRandomBool() ) );
            dvs.add( new TrackedEntityDataValue( psi1, deOpv, date.toDate(), getRandomOptionSetCode( osOpv ) ) );
            dvs.add( new TrackedEntityDataValue( psi1, deInfFeed, date.toDate(), getRandomOptionSetCode( osInfFeed ) ) );
            
            dvs.add( new TrackedEntityDataValue( psi2, deInfWeight, date.toDate(), String.valueOf( ( 2500 + new Random().nextInt( 1500 ) ) ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deInfFeed, date.toDate(), getRandomOptionSetCode( osInfFeed ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deMeasles, date.toDate(), getRandomBool() ) );
            dvs.add( new TrackedEntityDataValue( psi2, dePenta, date.toDate(), getRandomOptionSetCode( osPenta ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deYelFev, date.toDate(), getRandomBool() ) );
            dvs.add( new TrackedEntityDataValue( psi2, deIpt, date.toDate(), getRandomOptionSetCode( osIpt ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deDpt, date.toDate(), getRandomOptionSetCode( osDpt ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deVitA, date.toDate(), getRandomBool() ) );
            dvs.add( new TrackedEntityDataValue( psi2, deHivRes, date.toDate(), getRandomOptionSetCode( osHivRes ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deHivTest, date.toDate(), getRandomOptionSetCode( osHivTest ) ) );
            dvs.add( new TrackedEntityDataValue( psi2, deChildArv, date.toDate(), getRandomOptionSetCode( osChildArv ) ) );
            
            for ( TrackedEntityDataValue dv : dvs )
            {
                dataValueService.saveTrackedEntityDataValue( dv );
            }

            c++;
            
            log.info( "Created tracked entity instance " + c + ": " + tei.getUid() + ", " + values[0] + " " + values[1] + " " + values[2] + ", values: " + dvs.size() );
        }
    }
    
    private String getRandomOptionSetCode( OptionSet optionSet )
    {
        int no = optionSet.getOptions().size();
        int r = new Random().nextInt( no );
        return optionSet.getOptions().get( r ).getCode();        
    }
    
    private String getRandomBool()
    {
        return String.valueOf( new Random().nextBoolean() );
    }
}
