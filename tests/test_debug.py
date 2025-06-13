import logging
import pytest
from pyalma.debug import setup_paramiko

@pytest.fixture
def paramiko_logger():
    logger = logging.getLogger("paramiko")
    original_level = logger.level
    yield logger
    logger.setLevel(original_level)

def test_setup_paramiko_debug_true(paramiko_logger):
    setup_paramiko(debug=True)
    assert paramiko_logger.level == logging.DEBUG

def test_setup_paramiko_debug_false(paramiko_logger):
    setup_paramiko(debug=False)
    assert paramiko_logger.level == logging.WARNING