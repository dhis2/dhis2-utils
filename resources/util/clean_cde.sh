#!/bin/sh

# Removes verbose html from custom entry form e.g. produced by ms word.

# First argument is name of html form.

# Remove all tr attributes

sed -i 's/<tr[^>]*>/<tr>/g' $1

# Remove p open/end tags

sed -i 's/<p[^>]*>//g' $1
sed -i 's/<\/p>//g' $1

# Remove b open/end tags

sed -i 's/<b[^>]*>//g' $1
sed -i 's/<\/b>//g' $1

# Remove span open/end tags

sed -i 's/<span[^>]*>//g' $1
sed -i 's/<\/span>//g' $1

# Remove strong open/end tags

sed -i 's/<strong[^>]*>//g' $1
sed -i 's/<\/strong>//g' $1

# Remove small open/end tags

sed -i 's/<small[^>]*>//g' $1
sed -i 's/<\/small>//g' $1

# Remove font open/end tags

sed -i 's/<font[^>]*>//g' $1
sed -i 's/<\/font>//g' $1

# Remove all style, width, nowrap, valign, view attributes

sed -i 's/style="[^"]*"//g' $1
sed -i 's/width="[^"]*"//g' $1
sed -i 's/nowrap="[^"]*"//g' $1
sed -i 's/valign="[^"]*"//g' $1
sed -i 's/view="[^"]*"//g' $1
sed -i 's/bgcolor="[^"]*"//g' $1

# Remove weird stuff

sed -i 's/<!--1-->//g' $1
sed -i 's/&nbsp;//g' $1

# Put back correct style for input elements

sed -i 's/<input/<input style="width:7em;text-align:center;"/g' $1
