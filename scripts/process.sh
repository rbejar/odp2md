#!/bin/bash
echo Remember that you may need to source the right virtual environment first...
echo The first parameter must be the directory that contains the odp files
for filename in "$1/"*.odp; do    
    odpmkd -i "$filename" -x -m > $(basename "$filename" .odp).md
done 
