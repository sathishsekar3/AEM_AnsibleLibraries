import sys
sys.path.append("/etc/ansible/library/")
from ansible.module_utils.basic import AnsibleModule
import requests
from requests.auth import HTTPBasicAuth
import urllib
import sys

DOCUMENTATION = '''
---
module: aem_passwordchange
short_description: Change AEM user`s password
description:
    - Change AEM  user`s password
author: Sathish Sekar
notes: []
options:
     port:
         description: aem running on port 4502 / 8080
         required: true
         default: null
     oldPassword:
         description: Old AEM user`s password
         required: true
         default: null
     newPassword:
         description: New AEM user`s password
         required: true
         default: null
     user:
         description: user name
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
     state:
         description: state=change => changes the password
         required: true
         default: null

'''
EXAMPLES='''
- name: change password
  aem_passwordchange: adminpassword=admin1 user=admin port={{onport}} oldPassword=admin1 newPassword=admin state=change
'''

class aem_passwordchange():

      def __init__(self,module):
             self.module = module
             self.port = module.params['port']
             self.oldPassword = module.params['oldPassword']
             self.newPassword = module.params['newPassword']
             self.user = module.params['user']
             self.adminuser = module.params['adminuser']
             self.adminpassword = module.params['adminpassword']


      def userpath(self):
               pathurl = "http://localhost:"+self.port+"/bin/querybuilder.json"
               payload = {'type': 'rep:User', 'property': 'rep:authorizableId', 'property.value': self.user }
               p =  requests.get(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), params=payload)
               path = p.json()
               return(path['hits'][0]['path'])


      def change(self):
             if self.oldPassword == self.newPassword:
                  self.module.exit_json(msg="Skipping. Passwords match")
             else:
                 try:
                    path = self.userpath()
                 except:
                    self.module.exit_json(msg=" Skipping.  Password change not needed ")
                    sys.exit(1)
                 strings = {'Path' : path, '_charset_': 'utf-8'}
                 qs =  urllib.urlencode(strings)
                 pathurl = "http://localhost:"+self.port+"/crx/explorer/ui/setpassword.jsp?"+qs
                 payload = { 'plain': self.newPassword, 'verify': self.newPassword, 'old': self.oldPassword }
                 resp = requests.post(pathurl, auth=HTTPBasicAuth(self.adminuser, self.adminpassword), data=payload)
                 if 'Password successfully changed' in resp.text:
                        self.module.exit_json(msg="Password successfully changed")
                 else:
                        self.module.exit_json(msg="could not change password")



def main():
	module = AnsibleModule(
        argument_spec=dict(
            port=dict(required=True, type='str'),
            oldPassword=dict(required=True, type='str'),
            newPassword=dict(required=True, type='str'),
            user=dict(required=True, type='str'),
            adminuser=dict(required=False, type='str',default="admin"),
            adminpassword=dict(required=True, type='str'),
            state=dict(required=True, type='str')
        ),
        supports_check_mode=False
        )

        user = aem_passwordchange(module)
        if module.params['state'] == "change":
             user.change()

if __name__ == "__main__":
	main()
