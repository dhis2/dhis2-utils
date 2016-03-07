package org.hisp.dhis.adhoc.command;

import org.springframework.context.ApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;

public class ContextChecker
{

    public static void main( String[] args )
    {
        ApplicationContext ctx = new ClassPathXmlApplicationContext( "classpath*:/META-INF/dhis/beans.xml" );
        
        

    }

}
