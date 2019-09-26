package org.hisp.dhis.datageneration.domain;

import java.util.List;

import org.hisp.dhis.common.ValueType;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class DataElement
{
    private String uid;

    private ValueType valueType;

    private List<String> optionSet;
}
