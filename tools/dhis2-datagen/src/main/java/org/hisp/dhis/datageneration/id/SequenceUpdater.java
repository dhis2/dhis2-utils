package org.hisp.dhis.datageneration.id;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class SequenceUpdater
{
    private final JdbcTemplate jdbcTemplate;

    public SequenceUpdater( JdbcTemplate jdbcTemplate )
    {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void updateSequence( String seqName, Long value )
    {
        jdbcTemplate.execute( "ALTER SEQUENCE " + seqName + " RESTART WITH " + value );
    }
}
