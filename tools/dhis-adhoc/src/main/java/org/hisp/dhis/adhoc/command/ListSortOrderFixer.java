package org.hisp.dhis.adhoc.command;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.Executed;
import org.hisp.dhis.common.IdentifiableObjectManager;
import org.springframework.beans.factory.annotation.Autowired;

public class ListSortOrderFixer
{
    private static final Log log = LogFactory.getLog( ListSortOrderFixer.class );
    
    @Autowired
    private IdentifiableObjectManager idObjectManager;
    
    @Executed
    public void execute()
    {
        log.info( "Start list sort order fix" );
    }
}
