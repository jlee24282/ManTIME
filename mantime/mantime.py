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

'''It returns the ISO-TimeML-annotated input documents.'''
__author__ = "Michele Filannino <filannino.m@gmail.com>"
__version__ = "0.1"
__codename__ = "purple tempo"

import cPickle
import glob
import logging
import os
import json
import xml.etree.cElementTree as cElementTree

from classifier import IdentificationClassifier
from classifier import NormalisationClassifier
from classifier import RelationClassifier
from settings import PATH_MODEL_FOLDER
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class ManTIME(object):

    def __init__(self, reader, writer, extractor, model_name, pipeline=True,
                 domain='general'):
        assert domain in ('general', 'clinical')
        self.post_processing_pipeline = pipeline
        self.reader = reader
        self.writer = writer
        self.extractor = extractor
        self.documents = []
        self.model_name = model_name
        self.model_path = '{}/{}/model.pickle'.format(PATH_MODEL_FOLDER,
                                                      self.model_name)
        try:
            self.model = cPickle.load(open(os.path.abspath(self.model_path)))
            logging.info('{} model: loaded.'.format(self.model.name))
        except IOError:
            self.model = None
            logging.info('{} model: built.'.format(model_name))
        self.domain = domain

    def train(self, folder):
        folder = os.path.abspath(folder)
        #print '[mantime/mantime.py] folder: ' + folder
        assert os.path.isdir(folder), 'Folder doesn\'t exist.'

        identifier = IdentificationClassifier()
        normaliser = NormalisationClassifier()
        linker = RelationClassifier()

        # corpus collection
        input_files = os.path.join(folder, self.reader.file_filter)
        documents = sorted(glob.glob(input_files))

        for index, input_file in enumerate(documents, start=1):
            basename = os.path.basename(input_file)
            position = '[{}/{}]'.format(index, len(documents))
            try:
                logging.info('{} Doc {}.'.format(position, basename))
                #print 'test 1 '
                doc = self.extractor.extract(self.reader.parse(input_file))
                #print 'Test doc: ' + str(doc)
                self.documents.append(doc)
            except cElementTree.ParseError:
            #except:
                msg = '{} Doc {} skipped: parse error.'.format(position,
                                                               basename)
                logging.error(msg)
        # training models (identification and normalisation)
        modl = identifier.train(self.documents, self.model_name)
        modl = normaliser.train(self.documents, modl)
        modl = linker.train(self.documents, modl)
        self.model = modl
        # dumping models
        cPickle.dump(modl, open(self.model_path, 'w'))

        return modl

    def label(self, input_obj):
        #print str(self.model)
        #print "input obj: " + str(input_obj)
        # according to the type
        assert self.model, 'Model not loaded.'

        identifier = IdentificationClassifier()
        normaliser = NormalisationClassifier()
        linker = RelationClassifier()

        try:
            doc = self.extractor.extract(self.reader.parse(input_obj))
            annotated_doc = identifier.test([doc], self.model, self.post_processing_pipeline)
            annotated_doc = normaliser.test([doc], self.model, self.domain)
            annotated_doc = linker.test([doc], self.model)

            #annotated_doc = json.loads(str = str(annotated_doc).encode('ascii', 'ignore').decode('ascii', 'ignore'))
            output = self.writer.write(annotated_doc)
            return output

        except cElementTree.ParseError:
            msg = 'Document {} skipped: parse error.'.format(
                os.path.relpath(input_obj))
            logging.error(msg)
            return ['']

        except TypeError:
            msg = 'Document {} skipped: TypeError.'.format(
                os.path.relpath(input_obj))
            logging.error(msg)
            return ['']

        except UnicodeEncodeError:
            #print str(annotated_doc)
            try:
                doc = self.extractor.extract(self.reader.parse(input_obj))
                annotated_doc = identifier.test([doc], self.model, self.post_processing_pipeline)
                annotated_doc = normaliser.test([doc], self.model, self.domain)
                annotated_doc = linker.test([doc], self.model)

                annotated_doc = json.loads(str = str(annotated_doc).encode('ascii', 'ignore').decode('ascii', 'ignore'))
                output = self.writer.write(annotated_doc)
                return output
            except:
                msg = 'Document {} skipped: Unicode Error.'.format(os.path.relpath(input_obj))
                logging.error(msg)
                return ['']


        except RuntimeError:
            #print str(annotated_doc)
            msg = 'Document {} skipped: Unicode Error.'.format(
                os.path.relpath(input_obj))
            logging.error(msg)
            return ['']
