import sys
sys.path.append("/etc/ansible/library/")
from ansible.module_utils.basic import AnsibleModule
import requests
import time
import ast
import os
from requests.auth import HTTPBasicAuth
import shutil
from subprocess import Popen, PIPE
from aemup import aemup

class aem_package():


     def __init__(self,module):
         self.module = module
         self.port = module.params['port']
         self.instance = module.params['instance']
         self.package = ast.literal_eval(module.params['package'])
         self.adminuser = module.params['adminuser']
         self.adminpassword = module.params['adminpassword']
         self.username =  module.params['username']
         self.password = module.params['password']
         self.prefix = module.params['prefix']
         self.cache =  module.params['cache']
         self.cacheFolder = module.params['cacheFolder']
         self.up = aemup(port=self.port,instance=self.instance,sleepSeconds=120)
         self.overwrite = module.params['overwrite']


     def get_pkg_info(self,package):
             instanceup = self.up.up()
             if instanceup:
                 path = package['path']
                 group = package['group']
                 file = os.path.basename(path)
                 pathurl = "http://localhost:"+self.port+"/etc/packages/"+group+"/"+file+"/jcr:content/vlt:definition/lastUnpacked"
                 resp =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword))
                 if resp.status_code == 404:
                     self.exists = False
                 elif resp.status_code == 200:
                     self.exists = True
             else:
                  self.module.fail_json(changed=False,msg="Instance not up after restart")

     def download_pkg(self,package):
             path = package['path']
             group = package['group']
             url = self.prefix+path
             targetpath = "/apps/tmp"
             cache = self.cache
             cacheFolder = self.cacheFolder
             file = os.path.basename(url)

             ##blindly serve from cache if it exists
             if cache == "true" and os.path.isfile(cacheFolder+"/"+file):
                shutil.copy(cacheFolder+"/"+file, targetpath+"/"+file)
                msg="Serving "+file+" from cache folder"
                module.exit_json(changed=True,msg=msg)
                return

             if self.username != "" and self.password != "" :
	  	 creds="-u '"+ self.username +":"+ self.password +"'"

             cmd="curl --fail -S -s "+ creds+" "+url+" > "+targetpath+"/"+file

             p = Popen(cmd,shell=True, stdout=PIPE, stderr=PIPE)
             out,err = p.communicate()
             if err == "" or err == "null":
                 msg="Downloaded "+file+" under "+targetpath+" - Success"
                 self.downloaded = True
                 if cache == "true":
                    if not os.path.exists(cacheFolder):
                       os.makedirs(cacheFolder)
                    shutil.copy(targetpath+"/"+file, cacheFolder)

             else:
                msg="Error downloading "+"url: "+url+" file: "+file
                self.downloaded = False

     def install_pkg(self,package):
             path = package['path']
             group = package['group']
             url = self.prefix+path
             file = os.path.basename(url)
             cmd='curl -S -s -u admin:'+self.adminpassword+' -F file="@/apps/tmp/'+file+'" -F name="'+file+'" -F force=true -F install=true http://localhost:'+self.port+'/crx/packmgr/service.jsp'
             p = Popen(cmd,shell=True, stdout=PIPE, stderr=PIPE)
             out,err = p.communicate()
             if err == "" or err == "null":
                  self.installed = True
             else:
                 self.installed = False

     def present(self):
           self.get_pkg_info(self.package)
           if self.exists and self.overwrite != "true":
                self.module.exit_json(msg="package: "+os.path.basename(self.package['path'])+" already installed.  Skipping")
           else:
                self.download_pkg(self.package)
                if self.downloaded:
                     self.install_pkg(self.package)
                     if self.installed:
                            path = self.package['path']
                            file = os.path.basename(path)
                            remove = "rm -rf /apps/tmp/"+file
                            os.system(remove)
                            if self.package['restart']:
                                 cmd="service aem-"+self.instance+" restart"
                                 os.system(cmd)
                                 instanceup = self.up.up()
                                 if not instanceup:
                                     self.module.fail_json(changed=False,msg="Instance not up after restart")
                            self.module.exit_json(changed=True,msg="package: "+os.path.basename(self.package['path'])+" installed successfully")

                     else:
                          self.module.exit_json(msg="package: "+os.path.basename(self.package['path'])+" not installed successfully")

                else:
                    self.module.exit_json(msg="Error in downloading package: "+os.path.basename(self.package['path']))


def main():
	module = AnsibleModule(
        argument_spec=dict(
            port=dict(required=True, type='str'),
            instance=dict(required=True, type='str'),
            package=dict(required=True),
            adminuser=dict(required=False, type='str',default="admin"),
            adminpassword=dict(required=True, type='str'),
            username=dict(required=True, type='str'),
            password=dict(required=True, type='str'),
            prefix =dict(required=True, type='str'),
            state=dict(required=True, type='str'),
            overwrite=dict(required=False, type='str', default="false"),
            cache=dict(required=False, type='str', default=False),
            cacheFolder=dict(required=False, type='str', default="/apps/cache/")
        ),
        supports_check_mode=False
        )
        pkg = aem_package(module)
        if module.params['state'] == "install":
            pkg.present()


if __name__ == "__main__":
	main()
