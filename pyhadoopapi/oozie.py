from .client import Client
from .webhdfs import WebHDFS
import requests
from io import StringIO
import sys

JOB_TRACKER = 'jobTracker'
NAMENODE = 'nameNode'
OOZIE_APP_PATH = 'oozie.wf.application.path'

def write_property(xml,name,value):
   xml.write('<property>\n')
   xml.write('<name>')
   xml.write(name)
   xml.write('</name>\n')
   xml.write('<value>')
   if type(value)==bool:
      if value:
         xml.write('true')
      else:
         xml.write('false')
   else:
      xml.write(str(value))
   xml.write('</value>\n')
   xml.write('</property>\n')

class Job:
   def __init__(self,oozie,path,namenode='sandbox'):
      self.oozie = oozie
      self.path = path
      if self.path[0]!='/':
         self.path = '/'+self.path
      if self.path[-1]=='/':
         self.path = self.path[0:-1]
      self.namenode = namenode

   def copy_resource(self,data,resource_path,overwrite=False):
      return self.oozie.webhdfs.copy(data,self.path + '/' + resource_path,overwrite=overwrite)

   def define_workflow(self,data,overwrite=False):
      return self.copy_resource(data,'workflow.xml',overwrite=overwrite)


   def start(self,properties,verbose=False):
      xml = StringIO()
      xml.write('<?xml version="1.0" encoding="UTF-8"?>\n<configuration>\n')
      for name in properties:
         value = properties[name]
         write_property(xml,name,value)
      for name in self.oozie.properties:
         if name not in properties:
            write_property(xml,name,value)
      if OOZIE_APP_PATH not in properties:
         write_property(xml,OOZIE_APP_PATH,'hdfs://{}{}/workflow.xml'.format(self.namenode,self.path))
      if NAMENODE not in properties:
         write_property(xml,NAMENODE,'hdfs://{}'.format(self.namenode))
      xml.write('</configuration>\n')

      if verbose:
         sys.stderr.write(xml.getvalue())
         sys.stderr.write('\n')
         sys.stderr.write('Requesting job start...\n')
      return self.oozie.start(xml.getvalue())

class Oozie(Client):

   def __init__(self,base=None,secure=False,host='localhost',port=50070,gateway=None,username=None,password=None,namenode='sandbox',tracker=None):
      super().__init__(service='oozie/v1',base=base,secure=secure,host=host,port=port,gateway=gateway,username=username,password=password)
      self.webhdfs = WebHDFS(base=base,secure=secure,host=host,port=port,gateway=gateway,username=username,password=password)
      self.properties = {}
      self.defaultNamenode = namenode
      if tracker is not None:
         self.properties[JOB_TRACKER] = tracker

   def addProperty(self,name,value):
      self.properties[name] = value

   def removeProperty(self,name):
      return self.property.pop(name,None)

   def newJob(self,path,namenode=None):
      return Job(self,path,namenode=namenode if namenode is not None else self.defaultNamenode)

   def start(self,xml):
      headers = {'Content-Type' : 'application/xml; charset=UTF-8'}
      url = '{}/jobs?action=start'.format(self.service_url())
      #print(url)
      req = requests.post(
         url,
         auth=self.auth(),
         data=xml,
         headers=headers)
      #print(req.status_code)
      if req.status_code==201:
         msg = req.json()
         return msg['id']
      else:
         self._exception(req.status_code,'Cannot start job.')

   def status(self,jobid):
      url = '{}/job/{}'.format(self.service_url(),jobid)
      #print(url)
      req = requests.get(
         url,
         auth=self.auth())
      #print(req.status_code)
      if req.status_code==200:
         msg = req.json()
         return (req.status_code,msg)
      else:
         return (req.status_code,req.text)
