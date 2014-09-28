import unittest
import doctest
import xmi2odoo
import logging

logging.basicConfig(level=logging.CRITICAL)

def load_tests(loader, tests, ignore):
        tests.addTests(doctest.DocTestSuite(xmi2odoo.uml))
        tests.addTests(doctest.DocTestSuite(xmi2odoo.model))
        tests.addTests(doctest.DocTestSuite(xmi2odoo.builder))
        return tests

