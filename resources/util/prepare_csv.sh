#!/bin/sh

# Prepares list of names for import as CSV
# Removes weird stuff and wraps in quotes
# First argument is name of file

# Replace tabs with white spaces

sed -i 's/\t/ /g' $1

# Remove multiple white spaces

sed -i 's/ \{1,\}/ /g' $1

# Delete empty lines

sed -i '/^\s*$/d' $1

# Remove spaces/tabs at beginning of lines

sed -i 's/^\s//g' $1

# Remove spaces/tabs at end of lines

sed -i 's/\s$//g' $1

# Remove dots at end of lines

sed -i 's/\.$//g' $1

# Remove "number of" variants

sed -i 's/# of //g' $1
sed -i 's/# Of //g' $1
sed -i 's/# //g' $1
sed -i 's/number of //g' $1
sed -i 's/Number of //g' $1

# Wrap in quotes

sed -i 's/^.*$/"&"/g' $1

# Insert header line

sed -i '1s/^/name\n/' $1
