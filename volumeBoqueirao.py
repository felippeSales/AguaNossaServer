import urllib2
from BeautifulSoup import BeautifulSoup

aesa = "http://site2.aesa.pb.gov.br/aesa/volumesAcudes.do?metodo=preparaUltimosVolumesPorBacia"

def read_link(src):
    sock = urllib2.urlopen(src)
    data = sock.read()
    sock.close()

    return data

def get_volume(acude):
    
    parser = BeautifulSoup(read_link(aesa))
    response = parser.prettify()
    
    achou = False
    count = 0
    
    for line in response.splitlines():
        if achou == False:
            if line.decode("latin-1").find(acude) > -1:
                achou = True
        else:
            if count == 31:
                return line
            else:
                count += 1
                
    
#print float(get_volume("Pessoa")) + 0.1
    