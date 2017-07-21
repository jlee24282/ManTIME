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

'''It uses the external CRFs algorithms to predict the labels.'''

from __future__ import division
from abc import ABCMeta, abstractmethod
import subprocess
import re
import codecs
import cPickle
from itertools import permutations
import logging
import os
import shutil
import multiprocessing
from tempfile import NamedTemporaryFile

from crf_utilities import get_scale_factors
from crf_utilities import probabilistic_correction
from crf_utilities import label_switcher
from attributes_extractor import TemporalRelationExtractor
from model.data import Event
from model.data import TemporalExpression
from model.data import TemporalLink
from model.document import SequenceLabel
from settings import PATH_MODEL_FOLDER
from settings import PATH_CRF_PP_ENGINE_TEST
from settings import PATH_CRF_PP_ENGINE_TRAIN
from settings import EVENT_ATTRIBUTES
from settings import NO_ATTRIBUTE
from settings import SENTENCE_WINDOW_RELATION
from utilities import Mute_stderr
from utilities import extractors_stamp


def identification_attribute_matrix(documents, dest, subject, training=True):
    """It writes in dest the entire training matrix for the identification.

    """
    assert type(documents) == list, 'Wrong type for documents.'
    assert len(documents) > 0, 'Empty documents list.'
    assert subject in ('EVENT', 'TIMEX'), 'Wrong identification subject.'

    # It stores the attribute matrix
    with codecs.open(dest, 'w', encoding='utf8') as matrix:
        for document in documents:
            for sentence in document.sentences:
                for word in sentence.words:
                    row = [v for _, v in sorted(word.attributes.items())]
                    matrix.write('\t'.join(row))
                    gold_label = word.gold_label.copy()

                    if not gold_label.is_out():
                        # The class of the instances different from the subject
                        # are changed in 'O'
                        if subject == 'EVENT':
                            if gold_label.is_timex():
                                gold_label.set_out()
                            else:
                                # For events, we use the attribute CLASS.
                                try:
                                    gold_label.tag = word.tag_attributes[
                                        'class']
                                except KeyError:
                                    # the clinical event type in i2b2 are
                                    # annotated with the attribute 'TYPE'.
                                    gold_label.tag = word.tag_attributes[
                                        'type']
                        else:
                            if gold_label.is_event():
                                gold_label.set_out()
                    if training:
                        matrix.write('\t' + str(gold_label))
                    matrix.write('\n')
                matrix.write('\n')
        matrix.close()


def normalisation_attribute_matrix(documents, dest, subject, training=True):
    """It writes in dest the entire training matrix for the attribute.

    """
    assert type(documents) == list, 'Wrong type for documents.'
    assert len(documents) > 0, 'Empty documents list.'
    assert subject in EVENT_ATTRIBUTES

    if training:
        get_label = lambda word: word.gold_label
    else:
        get_label = lambda word: word.predicted_label

    prev_label = get_label(documents[0].sentences[0].words[0])

    # It stores the attribute matrix
    with codecs.open(dest, 'w', encoding='utf8') as matrix:
        for ndoc, document in enumerate(documents):
            for nsen, sentence in enumerate(document.sentences):
                for nwor, word in enumerate(sentence.words):
                    # attributes:
                    row = [v for _, v
                           in sorted(word.attributes.items())]

                    # identification label:
                    # I keep only the EVENT label (not TIMEX)
                    ident_label = get_label(word)
                    if ident_label.is_timex():
                        ident_label.set_out()
                    row.append(str(ident_label))

                    # discard words that are not positively labelled
                    if ident_label.is_out():
                        prev_label = ident_label
                        continue

                    # group sequences by identification label
                    if str(prev_label) != str(ident_label):
                        matrix.write('\n')

                    # normalisation label (CLASS) for training
                    if training:
                        label = word.tag_attributes.get(subject, NO_ATTRIBUTE)

                        # Different null representation are collapsed.
                        label_to_be_fixed = any((not label, label == 'None',
                                                 ident_label.is_out()))
                        if label_to_be_fixed:
                            label = NO_ATTRIBUTE

                        label = label.replace(' ', '_').upper()
                        row.append(label)

                    # token coordinates for test purpose
                    else:
                        # I sneak in the coordinates of each token
                        row.append('{}_{}_{}'.format(ndoc, nsen, nwor))
                    matrix.write('\t'.join(row))

                    # I am using CRFs with singleton sequences
                    matrix.write('\n')

                    prev_label = ident_label
        matrix.close()


def relation_matrix(documents, dest, training=True):
    """ It writes in dest an entire feature matrix for the relations.

    """
    assert type(documents) == list, 'Wrong type for documents.'
    assert len(documents) > 0, 'Empty documents list.'

    if training:
        annotations = lambda document: document.gold_annotations
    else:
        annotations = lambda document: document.predicted_annotations

    def sent_distance(obj1, obj2):
        return abs(obj1.id_sentence() - obj2.id_sentence())

    extractor = TemporalRelationExtractor()

    # It stores the attribute matrix
    features = {}
    with codecs.open(dest, 'w', encoding='utf8') as matrix:
        for doc_id, document in enumerate(documents):
            inverted_index = {(obj.from_obj.identifier(),
                               obj.to_obj.identifier()): obj.relation_type
                              for obj
                              in annotations(document).itervalues()
                              if type(obj) == TemporalLink}
            events = [e.identifier() for e in annotations(document).values()
                      if type(e) == Event]
            timexes = [t.identifier() for t in annotations(document).values()
                       if type(t) == TemporalExpression]
            candidated_objs = events + timexes
            for from_id, to_id in permutations(candidated_objs, 2):
                from_obj = annotations(document)[from_id]
                to_obj = annotations(document)[to_id]

                criteria_sent_distance = sent_distance(from_obj, to_obj) < \
                    SENTENCE_WINDOW_RELATION
                criteria_meta = from_obj.meta or to_obj.meta

                if criteria_meta or criteria_sent_distance:
                    if (from_id, to_id) in inverted_index.keys():
                        features = extractor.extract(
                            from_obj, to_obj, document)
                        row = [v.value for _, v in sorted(features.items())]
                        if training:
                            row.append(inverted_index[(from_id, to_id)])
                    elif (to_id, from_id) in inverted_index.keys():
                        features = extractor.extract(
                            to_obj, from_obj, document)
                        row = [v.value for _, v in sorted(features.items())]
                        if training:
                            row.append(TemporalRelationExtractor.flip_relation(
                                inverted_index[(to_id, from_id)]))
                    else:
                        features = extractor.extract(
                            from_obj, to_obj, document)
                        row = [v.value for _, v in sorted(features.items())]
                        if training:
                            row.append('O')
                    if not training:
                        # I sneak in the objects IDs
                        row.append('{}_{}_{}'.format(doc_id, from_id, to_id))
                    matrix.write('\t'.join(row))
                    matrix.write('\n\n')
    matrix.close()
    header = [name for name, _ in sorted(features.items())]
    return header


class Classifier(object):
    """This class is an abstract classifier for ManTIME."""
    __metaclass__ = ABCMeta

    def __init__(self):
        self.num_cores = multiprocessing.cpu_count()

    @abstractmethod
    def train(self, documents, model_name):
        """ It returns a ClassificationModel object.

        """
        assert len(set([d.annotation_format for d in documents])) == 1

    @abstractmethod
    def test(self, documents, model, post_processing_pipeline=False):
        """ It returns a List of <Document> (with .predicted_annotations
            filled in.)

        """
        pass


class IdentificationClassifier(Classifier):
    """This class is a CRF interface.

    """
    def __init__(self):
        super(IdentificationClassifier, self).__init__()

    def train(self, documents, model_name):
        """It returns a ClassificationModel object.

        """
        # TO-DO: feature extractor deve yieldare anziche' ritornare
        assert type(documents) == list, 'Wrong type for documents.'
        assert len(documents) > 0, 'Empty documents list.'

        model = ClassificationModel(model_name)

        # load the header into the model
        first_word = documents[0].sentences[0].words[0]
        header = [k for k, _ in sorted(first_word.attributes.items())]
        model.load_header(header)

        # search for the token_normalised attribute position
        token_normalised_pos = [p for p, a in enumerate(header)
                                if a.find('token_normalised') > -1][0]
        model.pp_pipeline_attribute_pos = token_normalised_pos

        # save trainingset to model_name.trainingset.class
        scaling_factors = {}
        for idnt_class in ('EVENT', 'TIMEX'):
            path_and_model = (PATH_MODEL_FOLDER, model.name, idnt_class)
            trainingset_path = '{}/{}/identification.trainingset.{}'.format(
                *path_and_model)
            identification_attribute_matrix(documents, trainingset_path,
                                            idnt_class)

            # save scale factors for post processing pipeline
            scaling_factors[idnt_class] = get_scale_factors(
                trainingset_path, token_normalised_pos)

            crf_command = [PATH_CRF_PP_ENGINE_TRAIN,
                           '-p', str(self.num_cores), model.path_topology,
                           trainingset_path, '{}.{}'.format(model.path,
                                                            idnt_class)]
            with Mute_stderr():
                process = subprocess.Popen(crf_command, stdout=subprocess.PIPE)
                _, _ = process.communicate()

            # TO-DO: Check if the script saves a model or returns an error
            logging.info('Identification CRF model ({}): trained.'.format(
                idnt_class))

        # save factors in the model
        model.load_scaling_factors(scaling_factors)

        return model

    def test(self, documents, model, post_processing_pipeline=False):
        """It returns the sequence of labels from the CRF classifier.

        It returns the same data structure (list of documents, of sentences,
        of words with the right labels.

        """
        logging.info('Identification: applying ML models.')
        if extractors_stamp() != model.extractors_md5:
            logging.warning('The feature extractor component is different ' +
                            'from the one used in the training!')

        if post_processing_pipeline:
            try:
                factors = cPickle.load(open(model.path_factors))
                logging.info('Scale factors loaded.')
            except IOError:
                post_processing_pipeline = False
                logging.warning('Scale factors not found.')

        for idnt_class in ('EVENT', 'TIMEX'):
            testset_path = NamedTemporaryFile(delete=False).name
            model_path = '{}.{}'.format(model.path, idnt_class)
            identification_attribute_matrix(documents, testset_path,
                                            idnt_class, training=False)
            if post_processing_pipeline:
                crf_command = [PATH_CRF_PP_ENGINE_TEST, '-v2', '-m',
                               model_path, testset_path]
            else:
                crf_command = [PATH_CRF_PP_ENGINE_TEST, '-m',
                               model_path, testset_path]

            # Draconianly check the input files
            assert os.path.isfile(model_path), 'Model not found!'
            assert os.stat(model_path).st_size > 0, 'Model is empty!'
            assert os.path.isfile(testset_path), 'Test set doesn\'t exist!'

            with Mute_stderr():
                process = subprocess.Popen(crf_command, stdout=subprocess.PIPE)

            n_doc, n_sent, n_word = 0, 0, 0

            # post-processing pipeline
            if post_processing_pipeline and factors:
                scale_factors = factors[idnt_class]
                lines = label_switcher(probabilistic_correction(
                    iter(process.stdout.readline, ''),
                    scale_factors, model.pp_pipeline_attribute_pos, model.num_of_features, .5),
                    scale_factors, model.pp_pipeline_attribute_pos, .87)
            else:
                lines = iter(process.stdout.readline, '')

            prev_element = None
            prev_label = SequenceLabel('O')
            n_timex, n_event = 1, 1
            for line in lines:
                line = line.strip()
                if line:
                    # read the predicted label (last column from CRF++)
                    predicted_class = line.split('\t')[-1]
                    curr_label = SequenceLabel(predicted_class)
                    # for events, the predicted label carries the event
                    # class and not just [IO]-EVENT. Therefore, I need to
                    # save the class in eclass variable and also change
                    # curr_label's tag to just 'EVENT'
                    if idnt_class == 'EVENT':
                        if not curr_label.is_out():
                            try:
                                eclass = curr_label.tag
                                curr_label.tag = 'EVENT'
                            except AttributeError:
                                curr_label.set_out()

                    curr_word = documents[n_doc].sentences[n_sent].words[n_word]

                    # Just consider not annotated the current word if it has
                    # been already positively annotated by another previous
                    # model. Notice that the order in the most general FOR loop
                    # of this script has an impact.

                    if not curr_word.predicted_label.is_out():
                        curr_label.set_out()

                    if curr_label != prev_label:
                        if prev_element:
                            documents[n_doc].predicted_annotations[
                                prev_element.identifier()] = prev_element
                        if curr_label.is_event():
                            prev_element = Event('e{}'.format(n_event),
                                                 [curr_word], eclass=eclass)
                            n_event += 1
                        elif curr_label.is_timex():
                            prev_element = TemporalExpression(
                                't{}'.format(n_timex), [curr_word])
                            n_timex += 1
                        else:
                            prev_element = None
                    else:
                        if not curr_label.is_out():
                            prev_element.append_word(curr_word)

                    if not curr_label.is_out():
                        curr_word.predicted_label = curr_label

                    prev_label = curr_label

                    n_word += 1

                    if len(documents[n_doc].sentences[n_sent].words) == n_word:
                        n_word = 0
                        n_sent += 1
                        if len(documents[n_doc].sentences) == n_sent:
                            n_word, n_sent = 0, 0
                            n_doc += 1

                # this is the sentence separator. the eventual annotation is
                # pushed into the document. This prevents the merging of an
                # annotation at the end of a sentence and at the beginning of a
                # new one.
                else:
                    if prev_element:
                        try:
                            documents[n_doc].predicted_annotations[
                                prev_element.identifier()] = prev_element
                        except IndexError:
                            # we are at the end of the document and n_doc has
                            # been already incremented. we need to add
                            # prev_element to the previous document.
                            documents[n_doc - 1].predicted_annotations[
                                prev_element.identifier()] = prev_element

        logging.info('Identification: done.')
        return documents


class NormalisationClassifier(Classifier):
    """This class is a CRF interface.

    """
    def __init__(self):
        super(NormalisationClassifier, self).__init__()
        self.attributes = EVENT_ATTRIBUTES

    def train(self, documents, model):
        """It returns a ClassificationModel object for event CLASS attributes.

        """
        # TO-DO: feature extractor deve yieldare anziche' ritornare
        assert type(documents) == list, 'Wrong type for documents.'
        assert len(documents) > 0, 'Empty documents list.'

        # save trainingset to model_name.trainingset.*attribute*
        for attribute in self.attributes:
            path_model_attribute = (PATH_MODEL_FOLDER, model.name, attribute)
            trainingset_path = '{}/{}/normalisation.trainingset.{}'.format(
                *path_model_attribute)
            normalisation_attribute_matrix(documents, trainingset_path,
                                           attribute, training=True)
            model_path = '{}.{}'.format(model.path_normalisation, attribute)
            crf_command = [PATH_CRF_PP_ENGINE_TRAIN, '-p', str(self.num_cores),
                           model.path_attribute_topology, trainingset_path,
                           model_path]

            with Mute_stderr():
                process = subprocess.Popen(crf_command, stdout=subprocess.PIPE)
                _, _ = process.communicate()

            # Weakly check the output models
            if not os.path.isfile(model_path):
                msg = 'Normalisation CRF model ({}): *not* trained.'
                logging.error(msg.format(attribute))
            else:
                msg = 'Normalisation CRF model ({}): trained.'
                logging.info(msg.format(attribute))
        return model

    def test(self, documents, model, domain='general'):
        """It returns the sequence of labels from the classifier.

        It returns the same data structure (list of documents, of sentences,
        of words with the right labels.

        """
        logging.info('Normalisation: applying ML models.')
        for attribute in self.attributes:
            testset_path = NamedTemporaryFile(delete=False).name
            model_path = '{}.{}'.format(model.path_normalisation, attribute)
            normalisation_attribute_matrix(documents, testset_path, attribute,
                                           training=False)
            crf_command = [PATH_CRF_PP_ENGINE_TEST, '-m', model_path,
                           testset_path]

            # Weakly check the input files
            if not os.path.isfile(model_path):
                logging.warning('Model doesn\'t exist at {}'.format(
                    model_path))
                continue
            else:
                if os.stat(model_path).st_size == 0:
                    msg = 'Normalisation model for {} is empty!'
                    logging.warning(msg.format(attribute.lower()))
                    continue
            if not os.path.isfile(testset_path):
                msg = 'Normalisation test set for {} doesn\'t exist at {}.'
                logging.error(msg.format(attribute.lower(), testset_path))
                continue

            with Mute_stderr():
                process = subprocess.Popen(crf_command, stdout=subprocess.PIPE,
                                           stderr=None, stdin=None)

                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line:
                        line = line.split('\t')
                        label = line[-1]
                        location = line[-2]
                        seq_label = SequenceLabel(line[-3])
                        if seq_label.is_event():
                            n_doc, n_sent, n_word = location.split('_')
                            documents[int(n_doc)]\
                                .sentences[int(n_sent)].words[int(n_word)]\
                                .tag_attributes[attribute] = label

                # close stdout
                process.stdout.close()
                process.wait()

            # delete testset
            os.remove(testset_path)

        # normalisation of temporal expressions and events
        for document in documents:
            for element in document.predicted_annotations.itervalues():
                if isinstance(element, Event):
                    element.normalise(document)
                elif isinstance(element, TemporalExpression):
                    utterance = document.dct.replace('-', '')
                    if domain == 'general':
                        element.normalise(document, utterance)
                    elif domain == 'clinical':
                        element.normalise(document, utterance, 'clinical')

        logging.info('Normalisation: done.')
        return documents


class RelationClassifier(Classifier):
    """This class is a CRF interface for the temporal linking classification.

    """
    def __init__(self):
        super(RelationClassifier, self).__init__()

    def train(self, documents, model):
        """ It returns a RelationModel object.

        """
        # TO-DO: feature extractor deve yieldare anziche' ritornare
        assert type(documents) == list, 'Wrong type for documents.'
        assert len(documents) > 0, 'Empty documents list.'

        path_model_attribute = (PATH_MODEL_FOLDER, model.name)
        trainingset_path = '{}/{}/relation.trainingset.TLINK'.format(
            *path_model_attribute)
        header = relation_matrix(documents, trainingset_path, training=True)
        model.load_relation_header(header)
        model_path = '{}'.format(model.path_relation)
        crf_command = [PATH_CRF_PP_ENGINE_TRAIN, '-p', str(self.num_cores),
                       model.path_relation_topology, trainingset_path,
                       model_path]

        with Mute_stderr():
            process = subprocess.Popen(crf_command, stdout=subprocess.PIPE)
            _, _ = process.communicate()

        # Weakly check the output models
        if not os.path.isfile(model_path):
            logging.error('Temporal relation model: *not* trained.')
        else:
            logging.error('Temporal relation model: trained.')
        return model

    def test(self, documents, model):
        """ It returns a List of <Document> (with .predicted_annotations filled
            in.)

        """
        logging.info('Temporal relation extraction: applying ML models.')
        testset_path = NamedTemporaryFile(delete=False).name
        relation_matrix(documents, testset_path, training=False)
        crf_command = [PATH_CRF_PP_ENGINE_TEST, '-m', model.path_relation,
                       testset_path]

        # Weakly check the input files
        if not os.path.isfile(model.path_relation):
            logging.warning('Model doesn\'t exist at {}'.format(
                model.path_relation))
            return documents
        else:
            if os.stat(model.path_relation).st_size == 0:
                logging.warning('Relation model is empty!')
                return documents
        if not os.path.isfile(testset_path):
            msg = 'Temporal relation test set doesn\'t exist at {}.'
            logging.error(msg.format(testset_path))
            return documents

        with Mute_stderr():
            process = subprocess.Popen(crf_command, stdout=subprocess.PIPE,
                                       stderr=None, stdin=None)

            tlink_counter = 0
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:
                    line = line.split('\t')
                    relation_type = line[-1].strip()
                    if relation_type != 'O':
                        n_doc, from_id, to_id = line[-2].split('_')
                        n_doc = int(n_doc)
                        annotations = documents[n_doc].predicted_annotations
                        tlink_id = 'TL{}'.format(tlink_counter)
                        from_obj = annotations[from_id]
                        to_obj = annotations[to_id]
                        annotations[tlink_id] = TemporalLink(
                            tlink_id, from_obj, to_obj, relation_type)
                        tlink_counter += 1
            # close stdout
            process.stdout.close()
            process.wait()

        # delete testset
        os.remove(testset_path)

        logging.info('Temporal relation extraction: done.')
        return documents


class ClassificationModel(object):
    """Classification model.

    It just contains a time stamp of the files involved in the extraction
    of the attributes (nlp_functions.py) and their MD5-sum codes. I would
    like to be sure that the attribute set is compatible with the trained
    model. In order to check for it I'll check if the timestamps of the .pyc
    files are equal. Does something more elegant exists? I don't know.

    """
    def __init__(self, model_name):
        simplify = lambda name: re.sub(r'[\W]+', '', re.sub(r'\s+', '_', name))
        self.name = simplify(model_name)
        path_and_model = (PATH_MODEL_FOLDER, self.name)
        self.path = '{}/{}/identification.model'.format(*path_and_model)
        self.path_normalisation = '{}/{}/normalisation.model'.format(
            *path_and_model)
        self.path_relation = '{}/{}/relation.model'.format(*path_and_model)
        self.path_topology = '{}/{}/identification.template'.format(
            *path_and_model)
        self.path_attribute_topology = '{}/{}/attribute.template'.format(
            *path_and_model)
        self.path_relation_topology = '{}/{}/relation.template'.format(
            *path_and_model)
        self.path_header = '{}/{}/identification.header'.format(
            *path_and_model)
        self.path_relation_header = '{}/{}/relation.header'.format(
            *path_and_model)
        self.path_factors = '{}/{}/identification.factors'.format(
            *path_and_model)
        shutil.rmtree('{}/{}'.format(*path_and_model), ignore_errors=True)
        os.makedirs('{}/{}'.format(*path_and_model))
        self.num_of_features = 0
        self.topology = None
        self.relation_topology = None
        self.attribute_topology = None
        self.pp_pipeline_attribute_pos = None
        self.extractors_md5 = extractors_stamp()
        logging.info('Classification model: initialised.')

    def load_header(self, header):
        """It loads the header and stores it.

        """
        self.num_of_features = len(header)
        with open(self.path_header, 'w') as header_file:
            header_file.write('\n'.join(header))
        logging.info('Identification header: stored.')
        logging.info('Normalisation header: stored.')
        self.topology = self._generate_template()
        self._save_template(self.topology)
        self.attribute_topology = self._generate_template(True)
        self._save_template(self.attribute_topology, True)

    def load_relation_header(self, header):
        '''It loads the relation header and store it.

        '''
        self.num_of_relation_features = len(header)
        with open(self.path_relation_header, 'w') as header_file:
            header_file.write('\n'.join(header))
        logging.info('Temporal relation header: stored.')
        self.relation_topology = self._generate_template(relation=True)
        self._save_template(self.relation_topology, False, True)

    def load_scaling_factors(self, factors):
        cPickle.dump(factors, open(self.path_factors, 'w'))
        logging.info('Identification scaling factors: stored.')

    def _save_template(self, topology, attribute=False, relation=False):
        if attribute:
            dest = self.path_attribute_topology
        else:
            dest = self.path_topology
        if relation:
            dest = self.path_relation_topology
        with open(dest, 'w') as template:
            for pattern in topology:
                template.write(pattern)
                template.write('\n')
        logging.info(
            'CRF topology template (attribute={}, links={}): stored.'.format(
                attribute, relation))

    def _generate_template(self, attribute=False, relation=False):
        """It generates and dumps the CRF template for CRF++.

        """
        assert self.num_of_features > 0, 'Header not loaded yet.'

        n_of_features = self.num_of_features
        if attribute:
            n_of_features += 1
        if relation:
            n_of_features = self.num_of_relation_features

        patterns = set()
        for i in xrange(n_of_features):
            patterns.add('%x[0,{}]'.format(i))
            patterns.add('%x[-1,{}]'.format(i))
            patterns.add('%x[1,{}]'.format(i))
            patterns.add('%x[-2,{}]/%x[-1,{}]'.format(i, i))
            patterns.add('%x[-1,{}]/%x[0,{}]'.format(i, i))
            patterns.add('%x[0,{}]/%x[1,{}]'.format(i, i))
            patterns.add('%x[-1,{}]/%x[0,{}]/%x[1,{}]'.format(i, i, i))
            patterns.add('%x[0,{}]/%x[1,{}]/%x[2,{}]'.format(i, i, i))
            # Super light
            patterns.add('%x[1,{}]/%x[2,{}]'.format(i, i))
            patterns.add('%x[-2,{}]/%x[-1,{}]/%x[0,{}]'.format(i, i, i))
            patterns.add('%x[-1,{}]/%x[1,{}]'.format(i, i))
            patterns.add('%x[-2,{}]/%x[2,{}]'.format(i, i))
            # for m in sorted(list(set(range(num_of_features)) - set([i]))):
            #   template.add('%%x[0,%d]/%%x[0,%d]' % (i,m))
            #   template.add('%%x[-1,%d]/%%x[0,%d]' % (i,m))
            #   template.add('%%x[-1,%d]/%%x[0,%d]' % (m,i))
            #   template.add('%%x[-2,%d]/%%x[-1,%d]' % (i,m))
            #   template.add('%%x[-2,%d]/%%x[-1,%d]' % (m,i))
            #   template.add('%%x[0,%d]/%%x[1,%d]' % (i,m))
            #   template.add('%%x[0,%d]/%%x[1,%d]' % (m,i))
            #   template.add('%%x[1,%d]/%%x[2,%d]' % (i,m))
            #   template.add('%%x[1,%d]/%%x[2,%d]' % (m,i))
        topology = ['U{:0>7}:{}'.format(index, pattern)
                    for index, pattern
                    in enumerate(list(sorted(patterns)))]
        return topology
