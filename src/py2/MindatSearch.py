import sys, urllib3
from threading import Thread
from HTMLParser import HTMLParser
import osc

class MindatParser(HTMLParser):
    
    def __init__(self, osc_client=None):
        self.reset()
        self.wait_name = False
        self.wait_photo = False
        self.wait_formula = False
        self.osc_client = osc_client
        
    def handle_starttag(self, tag, attrs):
        #print("--- ", tag, " > ", attrs)
        
        '''
        if(self.wait_photo and tag == 'img'):
            for x in range(0, len(attrs)):
                if(attrs[x][0] == 'src' and 'imagecache' in attrs[x][1]):
                    self.wait_photo = False
                    print("URL https://www.mindat.org"+attrs[x][1])
                    self.osc_client.send('/url https://www.mindat.org'+attrs[x][1])
            self.wait_photo = False
        #'''
        
        
        #'''
        #print(tag)
        #if(self.wait_photo):
        #    for x in range(0, len(attrs)):
        #        print(tag, ' : ', attrs[x][0], ' > ', attrs[x][1])
            
        # ID newformula
        #if(tag == 'div'):
        #if(len(attrs) >= 1 and attrs[0][0] == 'class'):
        #    print(attrs[0][1])
        
        if(tag == 'div'):
            if(len(attrs) >= 1):
                if(attrs[0][0] == 'id'):
                    if(attrs[0][1] == 'introdata'):
                        self.wait_formula = True
                        self.formula = ""
        
        if(self.wait_photo and tag == 'a'):
            for x in range(0, len(attrs)):
                if(attrs[x][0] == 'href'):
                    if('photo' in attrs[x][1]):
                        self.wait_photo = False
                        print("PHOTO https://www.mindat.org"+attrs[x][1])
                        self.osc_client.send('/photo https://www.mindat.org'+attrs[x][1])
                    elif('min' in attrs[x][1]):
                        print("URL https://www.mindat.org"+attrs[x][1])    
                        self.osc_client.send('/url https://www.mindat.org'+attrs[x][1])
            self.wait_photo = False
        else:
            for x in range(0, len(attrs)):
                if(attrs[x][0] == 'class'):
                    if(attrs[x][1] == 'mineralheading'):
                        self.wait_name = True
                    elif('userbigpicture' in attrs[x][1]):
                        self.wait_photo = True
                    
                    #print " !!!!!!! FOUND NAME TAG : " + tag
        #if(attrs['class'] == ''):
        
    def handle_endtag(self, tag):
        if(self.wait_name == True):
            self.wait_name = False
        if(self.wait_formula == True and tag == 'div'):
            self.wait_formula = False
            if('Formula:' in self.formula):
                f = self.formula.split('Formula:')[1]
                print("FORMULA : ", f)
                self.osc_client.send('/formula '+ f)
            #print("FORMULA : "+self.formula)
        #elif(self.wait_photo == True and tag == 'div'):
        #    self.wait_photo = False
        #print("Encountered an end tag :", tag)

    def handle_data(self, data):
        if(self.wait_name == True):
            self.osc_client.send('/name '+ data)
            print("NAME : "+data)
        if(self.wait_formula == True):
            self.formula += data
        #print("Encountered some data  :", data)

class DownThread(Thread):
    def __init__(self, osc_client=None):
        Thread.__init__(self)
        self.osc_client = osc_client
        
    def run(self):
        http = urllib3.PoolManager()
        r = http.request('GET', 'https://www.mindat.org/randommin.php')
        parser = MindatParser(self.osc_client)
        parser.feed(r.data)

class MindatSearch:
    
    def __init__(self, osc_server_port=6660, osc_client_host='127.0.0.1', osc_client_port=6661):
        self.dest = 'fr'
        self.osc_client = osc.Client(osc_client_host, osc_client_port)
        self.osc_server = osc.Server(host='0.0.0.0', port=osc_server_port, callback=self.callback)
        self.osc_server.run(non_blocking=True)
        
        print("Mindat Search Ready")
    
    def callback(self, address, *args):
        if(address == '/random'):
            self.random()
        else:
            print("callback : "+str(address))
            for x in range(0,len(args)):
                print("     " + str(args[x]))
            
    def random(self):
        thd = DownThread(self.osc_client);
        thd.start();

if __name__ == '__main__':
    if len(sys.argv) == 1:
        MindatSearch();
    elif len(sys.argv) == 4:
        MindatSearch(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
    else:
        print('usage: %s <pyosc-server-port> <pyosc-client-host> <pyosc-client-port>')