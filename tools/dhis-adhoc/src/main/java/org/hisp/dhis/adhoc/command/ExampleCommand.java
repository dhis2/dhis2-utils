package org.hisp.dhis.adhoc.command;

import org.hisp.dhis.adhoc.Executed;
import org.springframework.transaction.annotation.Transactional;

public class ExampleCommand
{
    @Executed
    @Transactional
    public void execute()
    {
        // Do your stuff here
    }
}
