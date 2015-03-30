package org.hisp.dhis.adhoc.command;

import org.hisp.dhis.adhoc.Command;
import org.springframework.transaction.annotation.Transactional;

public class ExampleCommand
    implements Command
{
    @Override
    @Transactional
    public void execute()
        throws Exception
    {
        // Do your stuff here
    }
}
