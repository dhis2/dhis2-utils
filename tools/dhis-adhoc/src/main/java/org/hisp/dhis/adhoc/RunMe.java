package org.hisp.dhis.adhoc;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.system.util.AnnotationUtils;
import org.springframework.context.ApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;

/**
 * The purpose of this tool is to assist in performing ad-hoc tasks which
 * benefits from having the DHIS 2 service layer accessible. Examples of
 * such tasks are writing complex custom data entry forms to file and performing 
 * database operations which cannot be solved using SQL.
 * 
 * This class should be executed. You can do this e.g. by choosing "Run as" -
 * "Java application" in your IDE.
 * 
 * To add tasks one should:
 * 
 * <ol>
 * <li>Create a Java class</li>
 * <li>Annotate the method which performs the work with @Executed</li>
 * <li>Register the implementation class as a bean in beans.xml under src/main/resources/META-INF/dhis</li>
 * <li>Add the bean identifier to the list in the commands() method in this class</li>
 * </ol>
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
        return Arrays.asList( "randomEventPopulator" ); // Change this
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
            Object command = get( id );
            
            log.info( "Executing: " + id );
            
            invokeCommand( command );
            
            log.info( "Done: " + id );
        }
        
        log.info( "Process completed" );
    }
    
    private static Object get( String id )
    {
        return context.getBean( id );
    }
    
    private static void invokeCommand( Object object )
        throws Exception
    {
        List<Method> methods = AnnotationUtils.getAnnotatedMethods( object, Executed.class );
        
        if ( methods.size() != 1 )
        {
            log.warn( "Exactly one method must be annotated for execution on class: " + object.getClass() );
            return;
        }
        
        methods.get( 0 ).invoke( object, new Object[0] );
    }
}
