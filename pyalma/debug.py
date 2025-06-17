import logging

def setup_paramiko(debug=False):
    paramiko_logger = logging.getLogger("paramiko")
    paramiko_logger.setLevel(logging.WARNING)
    if debug:
        paramiko_logger.setLevel(logging.DEBUG)
