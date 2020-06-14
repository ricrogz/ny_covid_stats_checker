#! /usr/bin/env python
# this script filters output from ipython notebooks, for use in git repos
# http://stackoverflow.com/questions/18734739/using-ipython-notebooks-under-version-control
#
# put this file in a `bin` directory in your home directory, then run the following commands:
#
# chmod a+x ~/bin/ipynb_output_filter.py
# echo -e "*.ipynb \t filter=dropoutput_ipynb" >> ~/.gitattributes
# git config --global core.attributesfile ~/.gitattributes
# git config --global filter.dropoutput_ipynb.clean ~/bin/ipynb_output_filter.py
# git config --global filter.dropoutput_ipynb.smudge cat

# works with Notebook versions 3, 4 and 5 (iPython/Jupyter versions 2, 3 and 4)
import sys
from nbformat import read, write, NO_CONVERT

json_in = read(sys.stdin, NO_CONVERT)

# detect earlier versions
if ('worksheets' in json_in):
    # versions prior to 4 had a 'worksheets' field with a single element
    sheet = json_in.worksheets[0]
else:
    sheet = json_in

for cell in sheet.cells:
    if "outputs" in cell:
        cell.outputs = []
    if "prompt_number" in cell:
        cell.prompt_number = None
    if "execution_count" in cell:
        cell.execution_count = None

write(json_in, sys.stdout, NO_CONVERT)