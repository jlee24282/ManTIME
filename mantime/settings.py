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

'''This file containes some absolute paths you need to customize according to
you installation.'''

import os

HOME = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

LANGUAGE = 'english'

PATH_CRF_PP_ENGINE_TEST = os.path.abspath('/home/jamielee/CRF++-0.58/crf_test')
PATH_CRF_PP_ENGINE_TRAIN = os.path.abspath('/home/jamielee/CRF++-0.58/crf_learn')
PATH_CORENLP_FOLDER = os.path.abspath('/home/jamielee/ManTIME/corenlp-python/stanford-corenlp-full-2014-08-27/')

PATH_CRF_CONSISTENCY_MODULE = HOME + 'components/make_consistent.py'
PATH_CRF_ADJUSTMENT_MODULE = HOME + 'components/make_adjusted.py'
PATH_MODEL_FOLDER = './models'
EVENT_ATTRIBUTES = ('class', 'pos', 'tense', 'aspect', 'polarity', 'modality')
# EVENT_ATTRIBUTES = ('type', 'polarity', 'modality', 'sec_time_rel')
NO_ATTRIBUTE = 'n/a'
GAZETTEER_FOLDER = 'mantime/data/gazetteer/'
SENTENCE_WINDOW_RELATION = 1
