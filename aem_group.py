import sys
sys.path.append("/etc/ansible/library/")
from ansible.module_utils.basic import AnsibleModule
import requests
from requests.auth import HTTPBasicAuth
import yaml
from aemup import aemup

DOCUMENTATION = '''
---
module: aem_group
short_description: Creates/Deletes an AEM grp and adds users to a grp
description:
    - Creates/Deletes an AEM grp and adds users to a grp
author: Sathish Sekar
notes: []
options:
     group:
        description: group name
        required: true
        default: null
     users:
        description: users list that needs to be part of a group
        required: false
        default: dummy
     adminuser:
         description: aem instance admin username
         required: false
         default: admin
     adminpassword:
         description: aem instance admin password
         required: true
         default: null
     port:
         description: aem running on port 4502 / 8080
         required: true
         default: null
     state:
         description: state=present => creates a group
                      state=absent => deletes a group
                      state=add => adds users to a group
         required: true
         default: null
     instance:
         description: if its author / publish instance
         required: true
         default: null
'''
EXAMPLES='''
- name: Create Group
  aem_group: adminpassword=admin port={{onport}} state=present group=testgrp instance={{instance}}
- name: Delete a Group
  aem_group: adminpassword=admin port={{onport}} state=absent group=testgrp instance={{instance}}
- name: Add users to Group
  aem_group: adminpassword=admin users="[user1,user2]" port={{onport}} state=add group=administrators instance={{instance}}
'''

class aem_group():

        def __init__(self,module):
             self.module = module
             self.group = module.params['group']
             self.users = yaml.load(module.params['users'])
             self.adminuser = module.params['adminuser']
             self.adminpassword = module.params['adminpassword']
             self.port = module.params['port']
             self.instance = module.params['instance']
             self.up = aemup(port=self.port,instance=self.instance,sleepSeconds=120)

        def searchgroup(self):
             pathurl = "http://localhost:"+self.port+"/bin/security/authorizables.json"
             payload = { 'filter': self.group, '_charset_': 'utf-8' }
             p =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), params=payload)
             grpinfo = p.json()
             if grpinfo['authorizables']:
                   if grpinfo['authorizables'][0]['id'] == self.group:
                        self.exists = True
             else:
                 self.exists = False


        def creategrp(self):
             instanceup = self.up.up()
             if instanceup:
                 self.searchgroup()
                 if not self.exists:
                    pathurl = "http://localhost:"+self.port+"/libs/cq/security/authorizables/POST"
                    payload = { '_charset_': 'utf-8', 'groupName': self.group, 'givenName': self.group  }
                    resp = requests.post(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), data=payload)
                    if resp.status_code == 201:
                           self.module.exit_json(msg="Group "+self.group+" created successfully")
                    else:
                           self.module.exit_json(msg="Could not create group "+self.group)

                 else:
                    self.module.exit_json(msg="Group "+self.group+" already preset")
             else:
                 self.module.fail_json(changed=False,msg="Instance not up after restart")


        def existingmembers(self):
                pathurl = "http://localhost:"+self.port+"/libs/granite/security/search/authorizables.json?query=%7B%22scope%22%3A%7B%22groupName%22%3A%22"+self.group+"%22%7D%7D&_charset_=utf-8"
                p =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword))
                userlist = p.json()
                existingusrs = []
                for item in userlist['authorizables']:
                        existingusrs.append(item['authorizableId'])
                return(existingusrs)

        def grouppath(self):
               pathurl = "http://localhost:"+self.port+"/bin/querybuilder.json"
               payload = {'type': 'rep:Group', 'property': 'rep:authorizableId', 'property.value': self.group }
               p =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), params=payload)
               path = p.json()
               return(path['hits'][0]['path'])


        def adduserstogrp(self):
             instanceup = self.up.up()
             if instanceup:
                 self.searchgroup()
                 if self.exists:
                      usr = self.existingmembers()
                      for user in self.users:
                           usr.append(user)
                      path = self.grouppath()
                      pathurl = "http://localhost:"+self.port+path
                      fields = {'_charset_':'utf-8', 'memberAction': 'members'}
                      resp = requests.post(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword),files=fields,data={'memberEntry':usr} )
                      if resp.status_code == 200:
                           self.module.exit_json(msg="Added the users: "+str(usr)+" to the group administrators")
                      else:
                           self.module.exit_json(msg="Error adding users to the group administrators")

                 else:
                    self.module.exit_json(msg="Group "+self.group+" doesnt exists")
             else:
                 self.module.fail_json(changed=False,msg="Instance not up after restart")


        def delgrp(self):
             instanceup = self.up.up()
             if instanceup:
                 self.searchgroup()
                 if self.exists:
                     path = self.grouppath()
                     pathurl = "http://localhost:"+self.port+path
                     payload = {'_charset_':'utf-8', 'deleteAuthorizable': self.group}
                     resp = requests.post(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword),data=payload )
                     if resp.status_code == 200:
                          self.module.exit_json(msg="Group "+self.group+" deleted successfully!")
                     else:
                          self.module.exit_json(msg="Could not delete the group: "+self.group)
                 else:
                     self.module.exit_json(msg="Group "+self.group+" doesnt exists")
             else:
                 self.module.fail_json(changed=False,msg="Instance not up after restart")



def main():
	module = AnsibleModule(
        argument_spec=dict(
            group=dict(required=True, type='str'),
            users=dict(required=False, default="dummy"),
            adminuser=dict(required=False, type='str',default="admin"),
            adminpassword=dict(required=True, type='str'),
            port=dict(required=True, type='str'),
            state=dict(required=True, type='str'),
            instance=dict(required=True, type='str')
        ),
        supports_check_mode=False
        )
        grp = aem_group(module)
        if module.params['state'] == "present":
            grp.creategrp()
        elif module.params['state'] == "absent":
            grp.delgrp()
        elif module.params['state'] == "add":
            grp.adduserstogrp()


if __name__ == "__main__":
