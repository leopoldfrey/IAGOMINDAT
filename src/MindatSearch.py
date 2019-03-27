import sys, urllib3, certifi
from threading import Thread
#from HTMLParser import HTMLParser
#import osc
from html.parser import HTMLParser
from pyosc import Server
from pyosc import Client

class MindatParser(HTMLParser):
    
    def __init__(self, osc_client=None):
        super().__init__()
        self.reset()
        self.wait_name = False
        self.wait_photo = False
        self.wait_formula = False
        self.wait_result = False
        self.osc_client = osc_client
        
    def handle_starttag(self, tag, attrs):
        #print("--- ", tag, " > ", attrs)
        
        '''
        if(tag == 'div' or tag == 'h1'):
            if(len(attrs) >= 1):
                for x in range(0, len(attrs)):
                    if(attrs[x][0] == 'class'):
                        print(tag, ' : ', attrs[x][0], ' > ', attrs[x][1])
        #'''
               
        if(tag == 'div'):
            if(len(attrs) >= 1):
                if(attrs[0][0] == 'id'):
                    if(attrs[0][1] == 'introdata'):
                        self.wait_formula = True
                        self.formula = ""
        
        if(self.wait_result and tag == 'a'):
            for x in range(0, len(attrs)):
                if(attrs[x][0] == 'href'):
                    if('min' in attrs[x][1]):
                        print("--> URL https://www.mindat.org"+attrs[x][1])    
                        self.osc_client.send('/url', 'https://www.mindat.org/'+attrs[x][1])
        
        
        if(self.wait_photo and tag == 'a'):
            for x in range(0, len(attrs)):
                if(attrs[x][0] == 'href'):
                    if('photo' in attrs[x][1]):
                        self.wait_photo = False
                        print("--> PHOTO https://www.mindat.org"+attrs[x][1])
                        self.osc_client.send('/photo', 'https://www.mindat.org'+attrs[x][1])
                    elif('min' in attrs[x][1]):
                        print("--> URL https://www.mindat.org"+attrs[x][1])    
                        self.osc_client.send('/url', 'https://www.mindat.org/'+attrs[x][1])
            self.wait_photo = False
        
        else:
            for x in range(0, len(attrs)):
                if(attrs[x][0] == 'class'):
                    if('mineralheading' in attrs[x][1]):
                        #print("FOUND mineralheading")
                        self.wait_name = True
                    elif('userbigpicture' in attrs[x][1]):
                        #print("FOUND userbigpicture")
                        self.wait_photo = True
                    elif('newminsearchresults' in attrs[x][1]):
                        self.wait_result = True
        
    def handle_endtag(self, tag):
        if(self.wait_result == True):
            self.wait_result = False
        if(self.wait_name == True):
            self.wait_name = False
        if(self.wait_formula == True and tag == 'div'):
            self.wait_formula = False
            if('Formula:' in self.formula):
                f = self.formula.split('Formula:')[1]
                print("--> FORMULA : ", f)
                self.osc_client.send('/formula', f)

    def handle_data(self, data):
        if(self.wait_name == True or self.wait_result == True):
            self.osc_client.send('/name', data)
            print("--> NAME : "+data)
        if(self.wait_formula == True):
            self.formula += data

class DownThread(Thread):
    def __init__(self, osc_client=None, search='random'):
        Thread.__init__(self)
        self.search = search
        print("> SEARCH ", self.search)
        self.osc_client = osc_client
        
    def run(self):
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        if(self.search == 'random'):
            r = http.request('GET', 'https://www.mindat.org/randommin.php')
        else:
            r = http.request('GET', 'https://www.mindat.org/search.php?search='+self.search)
        parser = MindatParser(self.osc_client)
        parser.feed(str(r.data))
        parser.close()

class MindatSearch:
    
    def __init__(self, osc_server_port=6660, osc_client_host='127.0.0.1', osc_client_port=6661):
        self.dest = 'fr'
        
        self.osc_client = Client(osc_client_host, osc_client_port)
        self.osc_server = Server(host='0.0.0.0', port=osc_server_port, callback=self.callback)
        
        print("Mindat Search Ready")
    
    def callback(self, address, *args):
        if(address == '/random'):
            self.random()
        elif(address == '/search'):
            s = ""
            l = len(args)
            for x in range(0,l):
                s += str(args[x])
                if(x < (l-1)):
                    s += " "
            self.search(s)
        else:
            print("callback : "+str(address))
            for x in range(0,len(args)):
                print("     " + str(args[x]))
            
    def random(self):
        thd = DownThread(self.osc_client, "random")
        thd.start()
        
    def search(self, args):
        thd = DownThread(self.osc_client, args)
        thd.start()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        MindatSearch();
    elif len(sys.argv) == 4:
        MindatSearch(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
    else:
        print('usage: %s <pyosc-server-port> <pyosc-client-host> <pyosc-client-port>')