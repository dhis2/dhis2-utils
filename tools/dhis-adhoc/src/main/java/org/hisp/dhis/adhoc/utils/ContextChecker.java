package org.hisp.dhis.adhoc.utils;

import org.springframework.context.support.AbstractRefreshableApplicationContext;
import org.springframework.context.support.ClassPathXmlApplicationContext;

/**
 * Tests the Spring application context for circular dependencies.
 */
public class ContextChecker
{
    public static void main( String[] args )
    {
        AbstractRefreshableApplicationContext ctx = new ClassPathXmlApplicationContext(
            "classpath*:/META-INF/dhis/beans.xml" );
        ctx.setAllowCircularReferences( false );
        ctx.refresh();
        ctx.close();
    }
}
