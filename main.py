from collections import deque
import logging
import os
import ipaddress
import re
import csv
import pandas as pd
import glob
from time import time
logging.basicConfig(filename="parser_conf.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y:%M:%D:%H:%M:%S',
                    level=logging.ERROR)

class confparser():
    
    def __init__(self,extension='cfg',intended_block='#',conf_folder='conf_folder',result_folder='result'):
        logging.info("instance initialize")
        self.conflist = []
        self.conf_folder = conf_folder
        self.conf_re_group = []
        self.blocki = intended_block
        self.device_mgmtip = []
        self.result_folder = os.path.join(os.getcwd(),result_folder)
        self.allfiles = os.listdir()
        for f in self.allfiles:
            _, e = os.path.splitext(f)
            if extension in e:
                self.conflist.append(f)
        
        #remove all previous result
        for f in os.listdir(self.result_folder):
            os.remove(os.path.join(self.result_folder,f))
        logging.info("init finished, result in {} is {}".format(self.result_folder, os.listdir(self.result_folder)))

    def import_conf(self):
        #device_ip = 
        for conf in self.conflist:
            ipmapping = {"device_name":"","device_mgmt_ip":""}
            device_ip = os.path.basename(conf).split("_")[0]
            cur_device_conf = []
            with open(conf)  as f:
                self.fullconf = f.readlines()
                #init a list for capturing the content between two intended blocks
                
                s = []
                for cl in self.fullconf:
                    
                    if self.blocki not in cl:
                        s.append(cl)
                    else:
                        cur_device_conf.append(s)
                        s = []

                logging.info("regroup the configuration files in based on intend, details as following")
                logging.info(cur_device_conf)
                device_hostname = self.start_parse(cur_device_conf)
                ipmapping["device_name"] = device_hostname
                ipmapping["device_mgmt_ip"] = device_ip
                self.device_mgmtip.append(ipmapping)
        mapping_csv_columns = ['device_name','device_mgmt_ip']
        with open ("device_name_mgmtip.csv", 'a')  as f:
            writer = csv.DictWriter(f,fieldnames=mapping_csv_columns)
            writer.writeheader()
            for dict_data in self.device_mgmtip:
                writer.writerow(dict_data)
    def start_parse(self,cur_device_conf):
        interfaces =[]
        for c in cur_device_conf:
            try:
                if len(c) >0:
                    if "sysname" in c[0]:
                        lh=re.search(r'sysname (\S+)',c[0])
                        l_hostname = lh.group(1)
                        logging.info("found the hostname is {}".format(l_hostname))
                    if "interface " in c[0]:
                        interfaces.append(self.parse_interface(c,l_hostname))
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
                    logging.info(interfaces)
                    csv_columns = ['device','name','IPV4-Address','IPV4-MASK','IPV4-Subnet','VIP','VRRP-Group','description','Port-Type','Trunk-Allowed-VLAN','mode','VRF','IPV6','eth-trunk-member']
                    logging.info("start to write interface info to csv file of device {}".format(l_hostname))
                    h_i = l_hostname+'_interfaces.csv'
                    interface_csv = os.path.join(self.result_folder,h_i)


            except Exception as e:
                logging.info(e)    
        with open (interface_csv, 'a')  as f:
            writer = csv.DictWriter(f,fieldnames=csv_columns)
            writer.writeheader()
            for dict_data in interfaces:
                writer.writerow(dict_data)        
        return(l_hostname)

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
            'eth-trunk-member': '',
            'VIP':'',
            'VRRP-Group':''
        }
        for conf in conf_section:
            try:
                if "interface " in conf:
                    r = re.search(r'^interface (\S+)',conf)
                    intface_template["name"] = r.group(1)
                if "description" in conf:
                    r = re.search(r'description (.*)$',conf)
                    intface_template["description"] = r.group(1)
                if "port link-type" in conf:
                    r = re.search(r'port link-type (\S+)',conf)
                    intface_template["Port-Type"] = r.group(1)
                if "port trunk allow-pass vlan" in conf:
                    r = re.search(r'port trunk allow-pass vlan (.*)$',conf)
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
                if "vrrp" in conf:
                    r = re.search(r" vrrp vrid (\d{1,3}).*\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",conf)
                    intface_template["VIP"] = r.group(2)
                    intface_template["VRRP-Group"] = r.group(1)
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

    def sort_out_conf_folder(self):
        #first start from working path, all conf folders should be in \\self.conf_folder path
        logging.info("all device configurations should be in folder {}".format(self.conf_folder))
        working_path = os.getcwd()
        folders = os.listdir(working_path)
        conf_folder_path = os.path.join(os.getcwd(),self.conf_folder)
        if self.conf_folder not in folders:
            logging.error("no configuration folders was found")
            os.mkdir(conf_folder_path)
        else:
            pass
         
        conf_folders = []
        conf_files = []
        device_conf_list = []
        #find all device configuration folders
        #from Esight conf folder named as 172.23.32.2_20201216084952_startup.cfg
        #assumed situation is, a lot of conf from same device are saved in the same folder named with device Mgmt IP
        #need find the lastest one, the conf stand out of the folders should be unique
        #and there is no sub folder inside in the parent folders for device conf backup
        f_f = os.listdir(conf_folder_path)
        for f in f_f:
            f_path = os.path.join(conf_folder_path,f)
            if os.path.isdir(f_path):
                conf_folders.append(f_path)
            else:
                filename, fileextension = os.path.splitext(f_path)
                if fileextension == ".cfg":
                    conf_files.append(f_path)
        logging.info("all folders in the conf folder are found as following {}".format(conf_folders))
        '''
        conf files is something like this
        ['172.23.32.20_20210204003525_startup.cfg', '172.23.32.20_20210205003534_startup.cfg',\
        '172.23.32.20_20210222004136_running.cfg', '172.23.32.20_20210304004156_startup.cfg',\
        '172.23.32.20_20210304004159_running.cfg', '172.23.32.20_20210305003943_startup.cfg', \
        '172.23.32.20_20210305003952_running.cfg', '172.23.32.20_20210315003851_startup.cfg', \
        '172.23.32.20_20210315003903_running.cfg', '172.23.32.20_20210420004734_startup.cfg', \
        '172.23.32.20_20210420004746_running.cfg', '172.23.32.20_20210608004524_startup.cfg', \
        '172.23.32.20_20210608004539_running.cfg', '172.23.32.20_20210614004700_startup.cfg', ]
        '''

        for fd in conf_folders:
            logging.info("handling conf files in directory {}".format(fd))
            conf_list = os.listdir(fd)
            running_conf_list = []
            startup_conf_list = []
            for s_conf_file in conf_list:
                if "_running.cfg" in s_conf_file:
                    running_conf_list.append(s_conf_file)
                else:
                    startup_conf_list.append(s_conf_file)
            excution_date_list = []
            for ss_conf_file in running_conf_list:
                device_ip, excution_date, conf_type = ss_conf_file.split("_")
                excution_date_list.append(excution_date)
            latest_r_conf = os.path.join(fd,device_ip+"_"+max(excution_date_list)+"_"+conf_type)
            filename, fileextension = os.path.splitext(latest_r_conf)
            if fileextension == ".cfg":
                conf_files.append(latest_r_conf)

        logging.info("found all lastest configuration files as following {}".format(conf_files))
        self.conflist = conf_files
        return conf_files

    def combine_csv(self):
        os.chdir(self.result_folder)
        extension = 'csv'
        all_interface_csv = [f for f in glob.glob('*.{}'.format(extension))]
        combined_csv = pd.concat([pd.read_csv(f) for f in all_interface_csv])
        combined_csv.to_csv("interface_summary.csv",index=False, encoding='utf-8-sig')

parser = confparser()
time_start = time()
print("script started")
all_latest_conf_files = parser.sort_out_conf_folder()
parser.import_conf()
parser.combine_csv()
print("script finished")
time_finished = time()
print("script takes {}".format(time_finished-time_start))
