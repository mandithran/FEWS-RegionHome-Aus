def clearDiagLastLine(diagFile=None):
    fd=open(diagFile,"r")
    d=fd.read()
    fd.close()
    m=d.split("\n")
    s="\n".join(m[:-1])
    fd=open(diagFile,"w+")
    for i in range(len(s)):
        fd.write(s[i])
    fd.close()

def write2DiagFile(errorLevel=None, note=None):
    string = "\n<line level=\"%s\" description=\"FROM PYTHON: %s\"/>\n" % (errorLevel, note)
    return string