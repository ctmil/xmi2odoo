import unittest
import doctest
import xmi2oerp

def load_tests(loader, tests, ignore):
        tests.addTests(doctest.DocTestSuite(xmi2oerp.uml))
        tests.addTests(doctest.DocTestSuite(xmi2oerp.model))
        tests.addTests(doctest.DocTestSuite(xmi2oerp.builder))
        return tests

