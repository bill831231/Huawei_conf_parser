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
    
    def __init__(self,extension='cfg',intended_block='#'):
        logging.info("instance initialize")
        self.conflist = []
        self.conf_re_group = []
        self.blocki = intended_block
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
                #init a list for capturing the content between two intended blocks
                
                s = []
                for cl in self.fullconf:
                    
                    if self.blocki not in cl:
                        s.append(cl)
                    else:
                        self.conf_re_group.append(s)
                        s = []

                logging.info("regroup the configuration files in based on intend, details as following")
                logging.info(self.conf_re_group)
            self.start_parse()
    
    def start_parse(self):
        for c in self.conf_re_group:
            if "system" in c[0]:
                lh=re.search(r'sysname (\S+)',c)
                l_hostname = lh.group(1)
            if "interface" in c[0]:
                self.parse_interface(c,l_hostname)
            if "router" in c[0]:
                    self.parse_routing(c,l_hostname)
            else:
                self.parse_system(c,l_hostname)

    def parse_system(self, c):
        pass

    def parse_routing(self,c):
        pass

    def parse_interface(self,c,l_hostname):
        for conf in c:
