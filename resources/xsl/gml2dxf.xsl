<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:gml="http://www.opengis.net/gml">

<xsl:template match="gml:coordinates">
  <coordinates><xsl:value-of select="."/></coordinates>
</xsl:template>

<xsl:template match="gml:Polygon">
  <feature type="Polygon">
    <xsl:apply-templates select=".//gml:coordinates"/>
  </feature>
</xsl:template>

<xsl:template match="gml:MultiPolygon">
  <feature type="MultiPolygon">
    <xsl:apply-templates select=".//gml:coordinates"/>
  </feature>
</xsl:template>

<xsl:template match="gml:Point">
  <feature type="Point">
    <xsl:apply-templates select=".//gml:coordinates"/>
  </feature>
</xsl:template>

<xsl:template match="gml:featureMember">
  <organisationUnit>
    <id>0</id>
    <uuid/>
    <name><xsl:value-of select=".//*[local-name()='Name']"/></name>
    <shortName><xsl:value-of select=".//*[local-name()='Name']"/></shortName>
    <code/>
    <openingDate/>
    <closedDate/>
    <active/>
    <comment/>
    <geoCode/>
    <xsl:apply-templates select="./child::node()/child::node()/gml:Polygon|./child::node()/child::node()/gml:MultiPolygon|./child::node()/child::node()/gml:Point"/>
    <lastUpdated/>
  </organisationUnit>
</xsl:template>

<xsl:template match="/">
<dxf xmlns="http://dhis2.org/schema/dxf/1.0" minorVersion="1.1">
<organisationUnits>
  <xsl:apply-templates select=".//gml:featureMember"/>
</organisationUnits>
</dxf>
</xsl:template>

</xsl:stylesheet>
