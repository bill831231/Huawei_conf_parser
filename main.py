from collections import deque
import logging
import os
import ipaddress
import re
logging.basicConfig(filename="DB_playground_with_checking_email.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y:%M:%D:%H:%M:%S',
                    level=logging.INFO)

class confparser():
    
    def __init__(self,extension='cfg'):
        logging.info("instance initialize")
        self.conflist = []
        self.conf_re_group=[]
        self.allfiles = os.listdir()
        for f in self.allfiles:
            _, e = os.path.splitext(f)
            if extension in e:
                self.conflist.append(f)
        logging.info("in the current path {}, found the following conf files".format(os.getcwd(),self.conflist))
        
    def import_conf(self):
        for conf in self.conflist:
            with open("testconf.cfg")  as f:
                self.fullconf = f.readlines()
                self.fullconf = deque(self.fullconf)
                while len(self.fullconf) > 2:
                    fc = self.fullconf.popleft()
                    if "#" in fc:
                        section_list= self.get_section(self.fullconf)
                        self.conf_re_group.append(section_list)     
                    else: 
                        pass

                logging.info("regroup the configuration files in based on intend, details as following")
                logging.info(self.conf_re_group)
            self.start_parse()
    
    def get_section(self,fullconf):
        s =[]
        while len(fullconf) > 2:
            a = fullconf.popleft()
            if "#" not in a:
                s.append(a)
            else:
                fullconf.appendleft(a)
                return s
    def start_parse(self):
        while len(self.conf_re_group) > 1:
            c = self.conf_re_group.pop(0)
            if "system" in c[0]:
                lh=re.search(r'sysname (\S+)',c)
                l_hostname = lh.group(1)
            if "interface" in c[0]:
                self.parse_interface(c)
            if "router" in c[0]:
                    self.parse_routing(c)
            else:
                self.parse_system(c)

    def parse_system(self, c):
        pass

    def parse_routing(self,c):
        pass

    def parse_interface(self,c):
        logging.info("found interface info, start analyze")
        
            


parser = confparser()
parser.import_conf() 


