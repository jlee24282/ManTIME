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

import argparse
import codecs
import glob
import logging
import os


def main():

        for doc in glob.glob('data/*'):
            basename = os.path.basename(doc)
            writein = os.path.join('./output/', basename)
            # if writein not in glob.glob('./output/*.*'):
            file_path = '.'.join(writein.split('.')[:-1])

            if os.path.exists(file_path):
                os.rename(file_path, file_path + '.tml')


if __name__ == '__main__':
    main()
