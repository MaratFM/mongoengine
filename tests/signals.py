# -*- coding: utf-8 -*-
import unittest

from mongoengine import *
from mongoengine import signals

signal_output = []


class SignalTests(unittest.TestCase):
    """
    Testing signals before/after saving and deleting.
    """

    def get_signal_output(self, fn, *args, **kwargs):
        # Flush any existing signal output
        global signal_output
        signal_output = []
        fn(*args, **kwargs)
        return signal_output

    def setUp(self):
        connect(db='mongoenginetest')
        class Author(Document):
            name = StringField()

            def __unicode__(self):
                return self.name

            @classmethod
            def pre_save(cls, instance, **kwargs):
                signal_output.append('pre_save signal, %s' % instance)

            @classmethod
            def post_save(cls, instance, **kwargs):
                signal_output.append('post_save signal, %s' % instance)
                if 'created' in kwargs:
                    if kwargs['created']:
                        signal_output.append('Is created')
                    else:
                        signal_output.append('Is updated')

            @classmethod
            def pre_delete(cls, instance, **kwargs):
                signal_output.append('pre_delete signal, %s' % instance)

            @classmethod
            def post_delete(cls, instance, **kwargs):
                signal_output.append('post_delete signal, %s' % instance)

        self.Author = Author

        # Save up the number of connected signals so that we can check at the end
        # that all the signals we register get properly unregistered (#9989)
        self.pre_signals = (len(signals.pre_save.receivers),
                       len(signals.post_save.receivers),
                       len(signals.pre_delete.receivers),
                       len(signals.post_delete.receivers))

        signals.pre_save.connect(Author.pre_save, sender=Author)
        signals.post_save.connect(Author.post_save, sender=Author)
        signals.pre_delete.connect(Author.pre_delete, sender=Author)
        signals.post_delete.connect(Author.post_delete, sender=Author)

    def tearDown(self):
        signals.post_delete.disconnect(self.Author.post_delete, sender=self.Author)
        signals.pre_delete.disconnect(self.Author.pre_delete, sender=self.Author)
        signals.post_save.disconnect(self.Author.post_save, sender=self.Author)
        signals.pre_save.disconnect(self.Author.pre_save, sender=self.Author)

        # Check that all our signals got disconnected properly.
        post_signals = (len(signals.pre_save.receivers),
                        len(signals.post_save.receivers),
                        len(signals.pre_delete.receivers),
                        len(signals.post_delete.receivers))

        self.assertEqual(self.pre_signals, post_signals)

    def test_model_signals(self):
        """ Model saves should throw some signals. """

        a1 = self.Author(name='Bill Shakespeare')
        self.assertEqual(self.get_signal_output(a1.save), [
            "pre_save signal, Bill Shakespeare",
            "post_save signal, Bill Shakespeare",
            "Is created"
        ])

        a1.reload()
        a1.name='William Shakespeare'
        self.assertEqual(self.get_signal_output(a1.save), [
            "pre_save signal, William Shakespeare",
            "post_save signal, William Shakespeare",
            "Is updated"
        ])

        self.assertEqual(self.get_signal_output(a1.delete), [
            'pre_delete signal, William Shakespeare',
            'post_delete signal, William Shakespeare',
        ])
