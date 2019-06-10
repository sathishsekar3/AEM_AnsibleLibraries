import sys
sys.path.append("/etc/ansible/library/")
from ansible.module_utils.basic import AnsibleModule
import requests
from requests.auth import HTTPBasicAuth
from aemup import aemup

DOCUMENTATION = '''
---
module: aem_user
short_description: Creates/Deletes an AEM user
description:
    - Creates/Deletes an AEM user
author: Sathish Sekar
notes: []
options:
     user:
         description: user name
         required: true
         default: null
     userpass:
         description: user password
         required: true
         default: null
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
         description: state=present => creates an user
                      state=absent => deletes an user
         required: true
         default: null
     instance:
         description: if its author / publish instance
         required: true
         default: null
'''
EXAMPLES='''
- name: create an user
  aem_user: adminpassword=admin user={{item.user}} userpass={{item.password}} port={{onport}} state=present instance={{instance}}
  with_items:
     - { user : user1 , password: user1 }
     - { user : user2 , password: user2 }
- name: delete an user
  aem_user: adminpassword=admin user={{item.user}} userpass={{item.password}} port={{onport}} state=absent instance={{instance}}
  with_items:
     - { user : user1 , password: user1 }
     - { user : user2 , password: user2 }
'''

class aem_user():

      def __init__(self,module):
               self.module = module
               self.user = module.params['user']
               self.userpass = module.params['userpass']
               self.adminuser = module.params['adminuser']
               self.adminpassword = module.params['adminpassword']
               self.port = module.params['port']
               self.instance = module.params['instance']
               self.up = aemup(port=self.port,instance=self.instance,sleepSeconds=120)

      def searchuser(self):
               pathurl = "http://localhost:"+self.port+"/bin/security/authorizables.json"
               payload = { 'filter': self.user, '_charset_': 'utf-8' }
               p =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), params=payload)
               userinfo = p.json()
               if userinfo['authorizables']:
                   if userinfo['authorizables'][0]['id'] == self.user:
                        self.exists = True
               else:
                   self.exists = False

      def createuser(self):
               instanceup = self.up.up()
               if instanceup:
                   self.searchuser()
                   if not self.exists:
                        pathurl = "http://localhost:"+self.port+"/libs/cq/security/authorizables/POST"
                        payload = { '_charset_': 'utf-8', 'rep:userId': self.user, 'familyName': self.user, 'rep:password': self.userpass, 'rep:password': self.userpass  }
                        resp = requests.post(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), data=payload)
                        if resp.status_code == 201:
                           self.module.exit_json(msg="User "+self.user+" created successfully")
                        else:
                            self.module.exit_json(msg="Could not create user "+self.user)

                   else:
                       self.module.exit_json(msg="User "+self.user+" already preset")
               else:
                    self.module.fail_json(changed=False,msg="Instance not up after restart")

      def userpath(self):
               pathurl = "http://localhost:"+self.port+"/bin/querybuilder.json"
               payload = {'type': 'rep:User', 'property': 'rep:authorizableId', 'property.value': self.user }
               p =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), params=payload)
               path = p.json()
               return(path['hits'][0]['path'])

      def deluser(self):
               instanceup = self.up.up()
               if instanceup:
                   self.searchuser()
                   if self.exists:
                       path = self.userpath()
                       pathurl = "http://localhost:"+self.port+path
                       payload = { '_charset_': 'utf-8', 'deleteAuthorizable': self.user  }
                       resp = requests.post(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), data=payload)
                       if resp.status_code == 200:
                           self.module.exit_json(msg="User "+self.user+" deleted successfully!")
                       else:
                            self.module.exit_json(msg="Could not delete the user: "+self.user)
                   else:
                       self.module.exit_json(msg="User "+self.user+" doesnt exists")
               else:
                   self.module.fail_json(changed=False,msg="Instance not up after restart")

def main():
	module = AnsibleModule(
        argument_spec=dict(
            user=dict(required=True, type='str'),
            userpass=dict(required=True, type='str'),
            adminuser=dict(required=False, type='str',default="admin"),
            adminpassword=dict(required=True, type='str'),
            port=dict(required=True, type='str'),
            state=dict(required=True, type='str'),
            instance=dict(required=True, type='str')
        ),
        supports_check_mode=False
        )
        User = aem_user(module)
        if module.params['state'] == "present":
            User.createuser()
        elif module.params['state'] == "absent":
            User.deluser()


if __name__ == "__main__":
