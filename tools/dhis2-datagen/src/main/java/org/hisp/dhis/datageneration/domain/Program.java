package org.hisp.dhis.datageneration.domain;

/*
 * Copyright (c) 2004-2019, University of Oslo
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 *
 * Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 * Neither the name of the HISP project nor the names of its contributors may
 * be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @author Luciano Fiandesio
 */
@Getter
@AllArgsConstructor
public class Program
{
    /**
     * Program Primary Key
     */
    private Long id;
    /**
     * Program UID
     */
    private String uid;

    /**
     * Program type (WITH_REGISTRATION or WITHOUT_REGISTRATION)
     *
     * WITH_REGISTRATION = Tracker Program
     * WITHOUT_REGISTRATION = Event Program
     */
    private String type;

    /**
     * The Tracked Entity Instance type associated to this program
     * If the Program is Event Type, this field value is 0
     */
    private Long teiType;

    /**
     * OrgUnits associated to this program
     */
    private List<OrgUnit> orgUnits;

    /**
     * The list of Program Stages for this program
     */
    private List<ProgramStage> stages;

    /**
     * The list of Attributes for this program
     */
    private List<ProgramAttribute> attributes;

    public OrgUnit getOrgUnit( int index )
    {

        return this.orgUnits.get( index );
    }
}
