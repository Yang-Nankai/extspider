# -*- coding: utf-8 -*-
from extspider.collection.run import run
from unittest import TestCase


class TestBigRun(TestCase):

    def test_big_run(self):
        run()
