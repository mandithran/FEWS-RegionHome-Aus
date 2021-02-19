def write2DiagFile(errorLevel=None, note=None):
    string = "<line level=\"%s\" description=\"FROM PYTHON: %s\"/>\n" % (errorLevel, note)
    return string