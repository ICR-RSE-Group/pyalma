import logging
from pyalma.debug import setup_paramiko

def test_setup_paramiko_debug_true(paramiko_logger):
    setup_paramiko(debug=True)
    assert paramiko_logger.level == logging.DEBUG

def test_setup_paramiko_debug_false(paramiko_logger):
    setup_paramiko(debug=False)
    assert paramiko_logger.level == logging.WARNING