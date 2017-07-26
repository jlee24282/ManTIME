#!/usr/bin/env python
#
#   Copyright 2014 Michele Filannino
#
#   gnTEAM, School of Computer Science, University of Manchester.
#   All rights reserved. This program and the accompanying materials
#   are made available under the terms of the GNU General Public License.
#
#   author: Michele Filannino
#   email:  filannim@cs.man.ac.uk
#
#   For details, see www.cs.man.ac.uk/~filannim/

"""It contains all the readers for ManTIME.

   A reader must have a parse() method which is responsible for reading the
   input file and return a Document object, which is our internal
   representation of any input document (whetever the format is).

   In order to force the existence of the parse() method I preferred Python
   interfaces to the duck typing practice.
"""

from readers import TempEval3FileReader
from writers import TempEval3Writer
from attributes_extractor import FullExtractor
import os.path


class HManTemporals():
    def __init__(self):
        self.reader = TempEval3FileReader()
        self.writer = TempEval3Writer()
        self.extractor = FullExtractor()

    # get one filename and modify the result & generate output
    def optimizedOutput(self, filename):
        basepath = os.path.dirname(__file__)
        heidelOutputDir = os.path.abspath(os.path.join(basepath, '..','heideltime/data/output_byline/', filename+'.txt'))
        mantimeOutputDir = os.path.abspath(os.path.join(basepath,'..','output/manOutput/', filename[6:len(filename)-4]+'.tml'))

        mdoc = self.extractor.extract(self.reader.parse(mantimeOutputDir))
        print str(mdoc)
        hdoc = self.extractor.extract(self.reader.parse(heidelOutputDir))
        print str(hdoc)

        # DATE - intersection

        # DURATION - get it from mantime

        # TIME - intersection

        # SET - get it from mantime


def main():
    '''Simple ugly non-elegant test.'''
    '''To run file process only'''
    hm = HManTemporals()
    hm.optimizedOutput('outputdata_20170129080634_0')


if __name__ == '__main__':
    main()
