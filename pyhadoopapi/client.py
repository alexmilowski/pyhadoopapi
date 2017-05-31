
class Client:

   def __init__(self,service='',base=None,secure=False,host='localhost',port=50070,gateway=None,username=None,password=None):
      self.service = service
      self.base = base
      if self.base is not None and self.base[-1]!='/':
         self.base = self.base + '/'
      self.secure = secure
      self.host = host
      self.port = port
      self.gateway = gateway
      self.username = username
      self.password = password

   def service_url(self):
      if self.base is not None:
         return self.base + service
      protocol = 'https' if self.secure else 'http'
      if self.gateway is None:
         return '{}://{}:{}/{}'.format(protocol,self.host,self.port,self.service)
      else:
         return '{}://{}:{}/gateway/{}/{}'.format(protocol,self.host,self.port,self.gateway,self.service)

   def auth(self):
      return (self.username,self.password) if self.username is not None else None

   def _exception(self,status,message):
      error = None;
      if status==401:
         error = PermissionError(message)
      else:
         error = IOError(message)
      error.status = status
      return error;
