package org.hisp.dhis.datageneration.domain;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ProgramStage
{
    private Long id;

    private String uid;

    private List<DataElement> dataElements;
}
