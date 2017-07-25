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

from abc import ABCMeta, abstractmethod
import cgi
import codecs
import cPickle
from datetime import datetime
import logging
from lxml import etree as letree
from operator import attrgetter
import os
import sys
from StringIO import StringIO
import tempfile
import xml.etree.cElementTree as etree



class HManTemporals():
    def __init__(self):
        pass

    #get one filename and modify the result & generate output
    def optimizedOutput(self, filename):
        heidelOutputDir = '' + filename
        mantimeOutputDir = '' + filename

        hDataFile = open(heidelOutputDir, 'r')
        mDataFile = open(mantimeOutputDir, 'r')

        hData = str(hDataFile.readlines())
        mData = str(mDataFile.readlines())

        #DATE

        #DURATION - get it from mantime

        #TIME

        #SET - get it from mantime

        hDataFile.close()
        mDataFile.close()



def main():
    '''Simple ugly non-elegant test.'''
    '''To run file process only'''
    hm = HManTemporals()
    hm.optimizedOutput()

if __name__ == '__main__':
    main()
