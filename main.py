from collections import deque
import logging
import os
import ipaddress
import re
import csv
logging.basicConfig(filename="parser_conf.log",
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
        self.interfaces = []
        self.allfiles = os.listdir()
        for f in self.allfiles:
            _, e = os.path.splitext(f)
            if extension in e:
                self.conflist.append(f)
        logging.info("in the current path {}, found the following conf files".format(os.getcwd(),self.conflist))

    def import_conf(self):
        for conf in self.conflist:
            with open(conf)  as f:
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
            
            if len(c) >0:
                if "sysname" in c[0]:
                    lh=re.search(r'sysname (\S+)',c[0])
                    l_hostname = lh.group(1)
                    logging.info("found the hostname is {}".format(l_hostname))
                if "interface" in c[0]:
                    self.interfaces.append(self.parse_interface(c,l_hostname))
                if "router" in c[0]:
                        self.parse_routing(c,l_hostname)
                else:
                    try: 
                        self.parse_system(c,l_hostname)
                    except Exception as e:
                        if e == UnboundLocalError:
                            pass
                        else:
                            logging.info(e)
            else:
                pass
        logging.info(self.interfaces)
        csv_columns = ['device','name','IPV4-Address','IPV4-MASK','IPV4-Subnet','description','Port-Type','Trunk-Allowed-VLAN','mode','VRF','IPV6','eth-trunk-member']
        logging.info("start to write interface info to csv file of device {}".format(l_hostname))
        with open (l_hostname+'_interfaces.csv', 'a')  as f:
            
            writer = csv.DictWriter(f,fieldnames=csv_columns)
            writer.writeheader()
            for ddd in self.interfaces:
                writer.writerow(ddd)
    def parse_system(self, c,l_hostname):
        pass

    def parse_routing(self,c,l_hostname):
        pass

    def parse_interface(self,conf_section,l_hostname):
        logging.info("start analyzing this conf section {}".format(conf_section))
        intface_template = {
            'device': l_hostname,
            'name' : '',
            'description' : '',
            'Port-Type' : '',
            'Trunk-Allowed-VLAN' : '',
            'mode' : '',
            'VRF' : '',
            'IPV4-Address' : '',
            'IPV4-MASK' : '',
            'IPV4-Subnet' : '',
            'IPV6': '',
            'eth-trunk-member': ''
        }
        for conf in conf_section:
            try:
                if "interface " in conf:
                    r = re.search(r'interface (\S+)',conf)
                    intface_template["name"] = r.group(1)
                if "description" in conf:
                    r = re.search(r'description (\S+.*?)',conf)
                    intface_template["description"] = r.group(1)
                if "port link-type" in conf:
                    r = re.search(r'port link-type (\S+)',conf)
                    intface_template["Port-Type"] = r.group(1)
                if "port trunk allow-pass vlan" in conf:
                    r = re.search(r'port trunk allow-pass vlan (\S+)',conf)
                    intface_template["Trunk-Allowed-VLAN"] = r.group(1)
                if "mode" in conf:
                    r = re.search(r'mode (\S+)',conf)
                    intface_template["mode"] = r.group(1)
                if "ip binding vpn-instance" in conf:
                    r = re.search(r'ip binding vpn-instance (\S+)',conf)
                    intface_template["VRF"] = r.group(1)
                if "ip address" in conf:
                    if "ip address dhcp-alloc" in conf:
                        intface_template["IPV4-Address"] = "DHCP"
                    else:
                        r = re.search(r'ip address (\S+) (\S+)',conf)
                        intface_template["IPV4-Address"] = r.group(1)
                        intface_template["IPV4-MASK"] = r.group(2)
                        ipinter = ipaddress.IPv4Interface(r.group(1)+'/'+r.group(2))
                        intface_template["IPV4-Subnet"] = ipinter.network
                if "ipv6 address" in conf:
                    r = re.search(r'ipv6 address (.*?)',conf)
                    intface_template["IPV6"] = r.group(1)
                if "eth-trunk " in conf:
                    r = re.search(r'eth\-trunk (\d+)',conf)
                    intface_template["eth-trunk-member"] = r.group(1)
            except Exception as e:
                logging.error("handling conf {} has error".format(conf))
                logging.error(e)

        return intface_template

        


parser = confparser()
parser.import_conf() 


