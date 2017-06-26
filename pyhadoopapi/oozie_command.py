from .oozie import Oozie
from .client import ServiceError
import argparse
import sys
import os
import json

def oozie_start_command(client,argv):
   cmdparser = argparse.ArgumentParser(prog='pyhadoopapi oozie start',description='start')
   cmdparser.add_argument(
      '-p','--property',
      dest='property',
      action='append',
      metavar=('name','value'),
      nargs=2,
      help="A property name/value pair (e.g., name=value)")
   cmdparser.add_argument(
      '-P','--properties',
      dest='properties',
      action='append',
      nargs=1,
      metavar=('file.json'),
      help="Property name/value pairs in JSON format.")
   cmdparser.add_argument(
      '-d','--definition',
      dest='definition',
      nargs=1,
      metavar=('file.xml'),
      help="The workflow definition to copy")
   cmdparser.add_argument(
      '-cp','--copy',
      dest='copy',
      action='append',
      metavar=('file or file=target'),
      nargs=1,
      help="A resource to copy (e.g., source or source=dest)")
   cmdparser.add_argument(
      '--namenode',
      nargs=1,
      metavar=('node[:port]'),
      help="The name node for jobs")
   cmdparser.add_argument(
      '--tracker',
      nargs=1,
      metavar=('node[:port]'),
      help="The job tracker for jobs")
   cmdparser.add_argument(
      '-v',
      action='store_true',
      dest='verbose',
      default=False,
      help="Verbose")
   cmdparser.add_argument(
      'path',
      help='The job path')
   args = cmdparser.parse_args(argv)
   if args.namenode is not None:
      client.namenode = args.namenode
   if args.tracker is not None:
      client.addProperty('jobTracker',args.tracker)

   job = client.newJob(args.path)
   if args.definition is not None:
      with open(args.definition,'rb') as data:
         if args.verbose:
            sys.stderr.write('{} → {}\n'.format(args.definition,'workflow.xml'))
         job.define_workflow(data,overwrite=True)
   properties = {}
   if args.properties is not None:
      for propfile in args.properties:
         with open(propfile[0]) as propfilein:
            data = json.load(propfilein)
            for name in data:
               properties[name] = data[name]
   if args.property is not None:
      for prop in args.property:
         properties[prop[0]] = prop[1]
   if args.copy is not None:
      for copy in args.copy:
         fpath = copy[0]
         eq = fpath.find('=')
         if eq==0:
            sys.stderr.write('invalid copy argument: '+fpath)
            sys.exit(1)
         elif eq>0:
            dest = fpath[eq+1:]
            fpath = fpath[0:eq]
         else:
            slash = fpath.rfind('/')
            dest = fpath[slash+1] if slash>=0 else fpath
         with open(fpath,'rb') as data:
            if args.verbose:
               sys.stderr.write('{} → {}\n'.format(fpath,dest))
            job.copy_resource(data,dest,overwrite=True)
   jobid = job.start(properties,verbose=args.verbose)
   print(jobid)

def oozie_status_command(client,argv):
   cmdparser = argparse.ArgumentParser(prog='pyhadoopapi oozie status',description='job status')
   cmdparser.add_argument(
      '-r','--raw',
      action='store_true',
      dest='raw',
      default=False,
      help="return raw JSON")
   cmdparser.add_argument(
      '-a',
      action='store_true',
      dest='actions',
      default=False,
      help="show error messages")
   cmdparser.add_argument(
      '-s','--show',
      dest='show',
      nargs='?',
      default='info',
      help="The information about the job to retrieve.")
   cmdparser.add_argument(
      '-l',
      action='store_true',
      dest='detailed',
      default=False,
      help="list details")
   cmdparser.add_argument(
      'jobids',
      nargs='*',
      help='a list job ids')
   args = cmdparser.parse_args(argv)
   if args.detailed:
      print('\t'.join(['JOB','STATUS','USER','PATH','START','END','CODE','MESSAGE']))

   for jobid in args.jobids:
      try:
         response = client.status(jobid,show=args.show)
         if args.raw or type(response)==str:
            if type(response)==str:
               sys.stdout.write(response)
            elif type(response)==bytes:
               sys.stdout.buffer.write(response)
            else:
               sys.stdout.write('\n')
               sys.stdout.write(json.dumps(response))
               sys.stdout.write('\x1e')
         elif args.detailed:
            startTime = response.get('startTime')
            endTime = response.get('endTime')
            lastModTime = response.get('lastModTime')
            createdTime = response.get('createdTime')
            appPath = response.get('appPath')
            status = response.get('status')
            actions = response.get('actions')
            user = response.get('user')
            print('\t'.join(map(lambda x:str(x),[jobid,status,user,appPath,startTime,endTime])))
            if args.actions and actions is not None:
               for action in actions:
                  print('\t'.join(map(lambda x:str(x) if x is not None else '',[action.get('id'),action.get('status'),user,action.get('name'),action.get('startTime'),action.get('endTime'),action.get('errorCode'),action.get('errorMessage')])))
         else:
            status = response.get('status')
            print('{}\t{}'.format(jobid,status))
            actions = response.get('actions')
            if args.actions and actions is not None:
               for action in actions:
                  print('{}\t{}\t{}\t{}'.format(action.get('id'),action.get('status'),action.get('errorCode'),action.get('errorMessage')))
      except ServiceError as err:
         if err.status_code==404:
            if args.raw:
               sys.stdout.write('\n')
               sys.stdout.write('{{"id":"{}","status":{}}}'.format(jobid,err.status_code))
               sys.stdout.write('\x1e')
            else:
               print('{}\tNOT FOUND'.format(jobid))
         else:
            if args.raw:
               sys.stdout.write('\n')
               sys.stdout.write('{{"id":"{}","status":{}}}'.format(jobid,err.status_code))
               sys.stdout.write('\x1e')
            else:
               raise

def oozie_ls_command(client,argv):
   cmdparser = argparse.ArgumentParser(prog='pyhadoopapi oozie status',description='job status')
   cmdparser.add_argument(
      '-a',
      action='store_true',
      dest='all',
      default=False,
      help="show all")
   cmdparser.add_argument(
      '-l',
      action='store_true',
      dest='detailed',
      default=False,
      help="list details")
   cmdparser.add_argument(
      '-s','--status',
      dest='status',
      nargs='?',
      default='RUNNING',
      help="filter by status")
   cmdparser.add_argument(
      '-o','--offset',
      nargs='?',
      dest='offset',
      type=int,
      default=0,
      metavar=('offset'),
      help="The offset at which to start")
   cmdparser.add_argument(
      '-n','--count',
      nargs='?',
      type=int,
      default=50,
      dest='count',
      metavar=('count'),
      help="The number of items to return")
   args = cmdparser.parse_args(argv)

   if args.all:
      msg = client.list_jobs(offset=args.offset,count=args.count)
   else:
      msg = client.list_jobs(offset=args.offset,count=args.count,status=args.status)
   if args.detailed:
      print('\t'.join(['ID','STATUS','NAME','USER','START','END']))
      for job in msg['workflows']:
         id = job['id']
         user = job['user']
         status = job['status']
         appName = job['appName']
         startTime = job['startTime']
         endTime = job['endTime']
         print('\t'.join(map(lambda x:str(x) if x is not None else '',[id,status,appName,user,startTime,endTime])))
   else:
      for job in msg['workflows']:
         id = job['id']
         print(id)


oozie_commands = {
   'start' : oozie_start_command,
   'status' : oozie_status_command,
   'ls' : oozie_ls_command
}

def oozie_command(args):

   client = Oozie(base=args.base,secure=args.secure,host=args.hostinfo[0],port=args.hostinfo[1],gateway=args.gateway,username=args.user[0],password=args.user[1])
   client.proxies = args.proxies
   client.verify = args.verify
   if args.verbose:
      client.enable_verbose()

   if len(args.command)==0:
      raise ValueError('One of the following comamnds must be specified: {}'.format(' '.join(oozie_commands.keys())))

   func = oozie_commands.get(args.command[0])
   if func is None:
      raise ValueError('Unrecognized command: {}'.format(args.command[0]))

   func(client,args.command[1:])
