import unittest


class TestSuiteGenerator:
    @staticmethod
    def generate(fn):
        return type(
            'TestCase_{0}'.format(fn.__name__),
            (unittest.TestCase,), {
                "runTest": lambda _ : fn()
            })