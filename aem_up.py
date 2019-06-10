#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import requests
import time

DOCUMENTATION = '''
---
module: aem_up
short_description: Checks if an AEM instance is up
description:
    - Checks if an AEM instance is up.
author: Sathish Sekar
notes: []
options:
   sleepSeconds:
       description:
            - it waits for the aem to come up within defined time period, if not it errors out.
       required: false
       default: 600 seconds

   port:
       description:
            - AEM instance port number
       required: true
       default: null
   instance:
       description:
            - AEM author or publish?
       required: true
       default: null
'''
EXAMPLES='''
aem_up: port={{onport}} instance={{instance}}
'''

class aem_up():

   def __init__(self,module):
        self.port = module.params['port']
        self.sleepSeconds = int(module.params['sleepSeconds'])
        self.instance = module.params['instance']
        self.module = module

   def healthcheck(self):
        while True:
            url = "http://localhost:"+self.port+"/libs/granite/core/content/login.html"
            headers = {"Connection": "close"}
            try:
               r = requests.get(url, timeout=.1,headers=headers)
               if r.status_code == 200 or r.status_code == 404 or r.status_code == 503:
                    search = r.content.find('QUICKSTART_HOMEPAGE')
                    return(search)
                    break
            except:
               continue

   def up(self):
       start_time = time.time()
       while True:
          rc = self.healthcheck()
          if rc != -1:
              msg="AEM "+self.instance+" is up"
              self.module.exit_json(msg=msg)
              break
          else:
              if time.time() - start_time > self.sleepSeconds:
                   self.module.fail_json(changed=False,msg='AEM '+str(self.instance)+' did not come up after '+str(self.sleepSeconds)+' seconds. Bad license file maybe?  Something else?')
              time.sleep(10)
              continue


def main():
	module = AnsibleModule(
        argument_spec=dict(
            sleepSeconds=dict(required=False, type='str',default="600"),
            port=dict(required=True, type='str'),
            instance=dict(required=True, type='str')
        ),
        supports_check_mode=False
        )
        I = aem_up(module)
        I.up()


if __name__ == "__main__":
	main()
