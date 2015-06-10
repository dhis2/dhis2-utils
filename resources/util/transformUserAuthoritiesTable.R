#Copyright (c) 2015, Jason P. Pickering
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, this
##   list of conditions and the following disclaimer. 
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#The views and conclusions contained in the software and documentation are those
#of the authors and should not be interpreted as representing official policies, 
#either expressed or implied.

#This script will transform a list of authorities into a DocBook appendix.

require(stringr)
#Set this to your source code directory
setwd("/home/jason/development/dhis2/dhis-2/dhis-web/dhis-web-maintenance/dhis-web-maintenance-user/src/main/resources/org/hisp/dhis/user/")
this.template.file<-"i18n_module.properties"
con <- file(this.template.file, "r", blocking = FALSE)
template<-readLines(con)
close(con)
template<-template[grepl("=",template)]
template<-template[grepl("^[MF]_*",template)]
template<-as.data.frame(str_split_fixed(template,"=",2))
template<-template[order(template(2))]
names(template)<-c("key","value_template")
template<-template[with(template, order(value_template)), ]
#Set as the output to your DHIS2 docbook source
output.dir<-"/home/jason/development/dhis2docs/src/docbkx/en/"
setwd(output.dir)
output.file<-"user_authorities_table.xml"
cat('<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<!DOCTYPE appendix PUBLIC "-//OASIS//DTD DocBook XML V4.4//EN" "docbookV4.4/docbookx.dtd" []>
<appendix>
  <title>User authorities</title>
  <table frame="all">
    <title/>
    <tgroup cols="3">
      <colspec colname="Authority Description"/>
      <colspec colname="System authority"/>
      <colspec colname="Description"/>
      <tbody>',file=output.file)

for (i in 1:nrow(template)) {
  
  cat("<row>",file=output.file,append=T)
  cat(paste0("<entry>",template[i,2],"</entry>"),file=output.file,append=T)
  cat(paste0("<entry>",template[i,1],"</entry>"),file=output.file,append=T)
  cat("<entry></entry>",file=output.file,append=T)
  cat("</row>",file=output.file,append=T)
}

cat("</tbody>
    </tgroup>
  </table>
</appendix>",file=output.file,append=T)