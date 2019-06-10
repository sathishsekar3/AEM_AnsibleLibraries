#!/usr/bin/python
import requests
import time

class aemup():

   def __init__(self,port,instance,sleepSeconds):
        self.port = port
        self.sleepSeconds = int(sleepSeconds)
        self.instance = instance

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
              instanceup = True
              return(instanceup)
              break
          else:
              if time.time() - start_time > self.sleepSeconds:
                 instanceup = False
                 return(instanceup)
              time.sleep(10)
              continue
