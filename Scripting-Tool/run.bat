@echo off
python C:\Users\y25ea\Desktop\BioschemasMarkupGenerator\Scripting-Tool\main.py^
 -g "https://github.com/BioSchemas/bioschemas.github.io/archive/master.zip"^
 -d "/bioschemas.github.io-master/_specifications/"^
 -t "/bioschemas.github.io-master/_types/"^
 -b "http://bio.sdo-bioschemas-227516.appspot.com/"^
 -s "https://schema.org/"^
 %*
