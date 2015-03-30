package org.hisp.dhis.adhoc.command;

import javax.annotation.Resource;

import org.hisp.dhis.adhoc.Command;
import org.hisp.dhis.analytics.scheduling.AnalyticsTableTask;
import org.hisp.dhis.system.scheduling.Scheduler;
import org.springframework.beans.factory.annotation.Autowired;

public class AnalyticsTableGenerator
    implements Command
{
    @Resource(name="analyticsAllTask")
    private AnalyticsTableTask analyticsTableTask;
    
    @Autowired
    private Scheduler scheduler;
    
    @Override
    public void execute()
        throws Exception
    {
        scheduler.executeTask( analyticsTableTask );        
    }
}
