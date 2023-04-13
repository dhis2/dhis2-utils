select 
ds.name as ds_name,
de.code as de_code, de.name as de_name, de.uid as de_uid, de.categorycomboid as de_cc,
cc.name as cc_name,
cocc.name as coc_name, cocc.code as coc_code,
p.name as pi_name, p.code as pi_code, p.attributevalues->'<attribute-uid>'->>'value' as pi_de, p.aggregateexportcategoryoptioncombo as p_aggre_coc

from dataset ds 

join datasetelement dsde on ds.datasetid=dsde.datasetid
join dataelement de on de.dataelementid=dsde.dataelementid 
join categorycombo cc on cc.categorycomboid=de.categorycomboid  
join categorycombos_optioncombos coc on coc.categorycomboid=cc.categorycomboid  
join categoryoptioncombo cocc on cocc.categoryoptioncomboid=coc.categoryoptioncomboid 
left join programindicator p on p.attributevalues->'<attribue-uid>'->>'value' = de.code and 
(p.aggregateexportcategoryoptioncombo=cocc.code or p.aggregateexportcategoryoptioncombo is null)

where ds.uid='<dataset-uid>';
