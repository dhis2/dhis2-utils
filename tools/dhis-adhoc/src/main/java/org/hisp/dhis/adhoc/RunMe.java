package org.hisp.dhis.adhoc;

import java.util.Arrays;
import java.util.List;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.context.ApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;

/**
 * The purpose of this tool is to assist in performing ad-hoc tasks which
 * benefits from having the DHIS 2 service layer accessible. Examples of
 * such tasks are writing complex custom data entry forms to file, generating
 * custom HTML or Jasper reports, and performing database operations which
 * cannot be solved using SQL.
 * 
 * This class should be executed. You can do this e.g. by choosing "Run as" -
 * "Java application" in your IDE.
 * 
 * To add tasks you should implement the Command interface, add your implementation
 * class as a bean in beans.xml under src/main/resources/META-INF/dhis, and add
 * the bean identifier to the list in the commands() method in this class.
 */
public class RunMe
{
    private static final Log log = LogFactory.getLog( RunMe.class );
    
    private static final String DHIS2_HOME = "/home/larshelg/dev/config/dhis2"; // Change this
    
    private static ApplicationContext context;
    
    /**
     * Add commands here by adding the bean identifier to the list.
     */
    public static List<String> commands()
    {
        return Arrays.asList( "randomEventPopulator" );
    }
    
    public static void main( String[] args )
        throws Exception
    {
        System.setProperty( "dhis2.home", DHIS2_HOME );
        
        log.info( "Initializing Spring context" );
        
        context = new ClassPathXmlApplicationContext( "classpath*:/META-INF/dhis/beans.xml" );
        
        log.info( "Spring context initialized" );
        
        for ( String id : commands() )
        {
            Command command = get( id );
            
            log.info( "Executing: " + id );
            
            command.execute();
            
            log.info( "Done: " + id );
        }
        
        log.info( "Process completed" );
    }
    
    private static Command get( String id )
    {
        return (Command) context.getBean( id );
    }
}
