#Copyright (c) 2014, Jason P. Pickering
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
#either expressed or implied, of the FreeBSD Project.

#This script will clean translation which do not exist in the templates
#The working directory should point to the head of the DHIS2 source code directory
#Period formats will also be removed, as they should never be translated

#Needed libraries
require(plyr)
require(stringr)
#If you are exeucting from the command line, you will need to give the working directory
args <- commandArgs(trailingOnly = TRUE)
wd<-args[1]
if (length(args) != 2) { stop("Usage: Rscript cleanTranslations.R DHIS2_SOURCE_DIR LANGUAGE_CODE") }
#A regular expression of language to clean
languages<-paste0("_",args[2])

allprops<-dir(wd, pattern = "i18.*\\.properties$", full.names = TRUE, recursive=TRUE)
allprops<-allprops[grepl("src",allprops)]
templates<-allprops[grepl("i18n_global\\.|i18n_module\\.",allprops)]
template.dirs<-gsub("i18n_global\\.properties|i18n_module\\.properties","",templates)
period.pattern<-"^format"

for (i in 1:length(template.dirs) ) {
#Start to loop through each template directory
this.template.file<-templates[i]
this.dir<-template.dirs[i]
this.files<-dir(this.dir,pattern = "i18.*\\_[a-z]{2}.properties$",full.names=TRUE)
this.files<-this.files[ grepl(languages,this.files) ]

if ( length(this.files) > 0 & !is.null(this.files) ) {
con <- file(this.template.file, "r", blocking = FALSE)
template<-readLines(con)
close(con)
template<-template[grepl("=",template)]
template<-as.data.frame(str_split_fixed(template,"=",2))
names(template)<-c("key","value_template")
template$template_order<-row.names(template)
#Remove the periods formats. They will never be translated
template<-template[!grepl("^format\\.",template$key),]
#Remove any duplicate keys as this causes big problems
template<-template[!duplicated(template$key),]

#Loop through each file, cleaning out needless translations
for (j in 1:length(this.files)) {
con <- file(this.files[j], "r", blocking = FALSE)
translation<-readLines(con)
close(con)
translation<-translation[grepl("=",translation)]
translation<-as.data.frame(str_split_fixed(translation,"=",2))
names(translation)<-c("key","value_translation")
translation<-merge(translation,template,by="key")
#Get differing translations
translation<-translation[as.character(translation$value_template) != as.character(translation$value_translation),]
#Remove any empty values
translation<-translation[as.character(translation$value_translation) != "",]
#Remove any duplicates
translation<-translation[!duplicated(translation),]
#Arrange as the same order as in the template
translation<-arrange(translation,template_order)
out<-paste0(translation$key,"=",translation$value_translation)
cat(out,file=this.files[j],sep="\r\n") 

} #Module loop
}# If statement
} #Main loop
