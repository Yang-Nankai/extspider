# -*- coding: utf-8 -*-
from extspider.collection.run import run
from unittest import TestCase, skip


class TestBigRun(TestCase):
    @skip
    def test_big_run(self):
        run()
