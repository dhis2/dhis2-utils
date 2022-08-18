#Author: Jason P. Pickering
#A simple script to refresh DHIS2 SQL views using R and curl
#Modify to suit your needs
username<-"admin"
password<-"district"
server<-"http://apps.dhis2.org/demo/"

#Do not modify below, unless you need to.
require(XML)
require(RCurl)
pass<-paste0(username,":",password)
url<-paste0(server,"/api/sqlViews.xml")
response<-getURL(url,userpwd=pass,httpauth = 1L, header=FALSE,ssl.verifypeer = FALSE)
doc<-xmlTreeParse(response, useInternal = TRUE)
top <- xmlRoot(doc)
urls<-as.list(xmlSApply(top[[2]], xmlGetAttr, "href"))
commands<-paste0('curl "',urls,'/execute" -X POST -u ',pass,' -v')
for (i in 1:length(commands)) {
system(commands[i]) }