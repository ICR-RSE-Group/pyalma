import logging

paramiko_logger = logging.getLogger("paramiko")
paramiko_logger.setLevel(logging.WARNING)

def setup_paramiko(debug=False):
    if debug:
        paramiko_logger.setLevel(logging.DEBUG)
