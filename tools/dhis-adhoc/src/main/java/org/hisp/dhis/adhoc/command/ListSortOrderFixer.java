package org.hisp.dhis.adhoc.command;

import java.util.Collections;
import java.util.Iterator;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.common.IdentifiableObjectManager;
import org.hisp.dhis.common.comparator.IdentifiableObjectCodeComparator;
import org.hisp.dhis.option.Option;
import org.hisp.dhis.option.OptionSet;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

public class ListSortOrderFixer
{
    private static final Log log = LogFactory.getLog( ListSortOrderFixer.class );
    
    @Autowired
    private IdentifiableObjectManager idObjectManager;
    
    @Executed
    @Transactional
    public void execute()
    {
        log.info( "Start list sort order fix" );
        
        OptionSet os = idObjectManager.get( OptionSet.class, "eUZ79clX7y1" ); // ICD10
        
        Iterator<Option> options = os.getOptions().iterator();
        
        while ( options.hasNext() )
        {
            if ( options.next() == null )
            {
                options.remove();
            }
        }
        
        Collections.sort( os.getOptions(), IdentifiableObjectCodeComparator.INSTANCE );
        
        idObjectManager.update( os );
    }
}
