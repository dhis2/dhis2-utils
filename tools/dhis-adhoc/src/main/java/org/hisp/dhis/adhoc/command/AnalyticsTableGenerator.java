package org.hisp.dhis.adhoc.command;

import javax.annotation.Resource;

import org.hisp.dhis.adhoc.annotation.Executed;
import org.hisp.dhis.analytics.scheduling.AnalyticsTableTask;
import org.hisp.dhis.system.scheduling.Scheduler;
import org.springframework.beans.factory.annotation.Autowired;

public class AnalyticsTableGenerator
{
    @Resource(name="analyticsAllTask")
    private AnalyticsTableTask analyticsTableTask;
    
    @Autowired
    private Scheduler scheduler;
    
    @Executed
    public void execute()
    {
        scheduler.executeTask( analyticsTableTask );        
    }
}
