#!/usr/bin/env python3
"""Local DFIR workflow kit; no automated attribution or compromise verdict."""
import argparse,csv,datetime as dt,hashlib,json,os,platform,shutil,subprocess,sys,urllib.request,urllib.parse
from pathlib import Path

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def record(case,action,**kw):
 with (case/'journal.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(dict(time=now(),action=action,**kw))+'\n')
def manifest(case):
 entries=[dict(path=p.relative_to(case).as_posix(),size=p.stat().st_size,sha256=digest(p)) for p in sorted(case.rglob('*')) if p.is_file() and p.name!='manifest.json']
 save(case/'manifest.json',dict(created=now(),files=entries))
def verify(case):
 data=json.loads((case/'manifest.json').read_text()); results=[]; known=set()
 for e in data['files']:
  p=(case/e['path']).resolve()
  if not p.is_relative_to(case.resolve()): raise ValueError('Unsafe manifest path')
  known.add(e['path']);results.append(dict(path=e['path'],ok=p.is_file() and digest(p)==e['sha256']))
 extras=[p.relative_to(case).as_posix() for p in case.rglob('*') if p.is_file() and p.name!='manifest.json' and p.relative_to(case).as_posix() not in known]
 print(json.dumps(dict(files=results,unlisted=extras),indent=2))
 return all(r['ok'] for r in results) and not extras

def run(case,name,argv,timeout=180):
 dest=case/'raw'/name
 dest.mkdir(parents=True,exist_ok=False)
 started=now()
 try:
  with (dest/'stdout.bin').open('wb') as out,(dest/'stderr.bin').open('wb') as err:
   p=subprocess.run(argv,stdout=out,stderr=err,timeout=timeout,check=False)
  record(case,'command',name=name,argv=argv,start=started,exit=p.returncode)
 except Exception as e: record(case,'command_error',name=name,argv=argv,error=str(e),start=started)

def collect_windows(case):
 if sys.platform!='win32': raise ValueError('Windows host required')
 ps={
 'processes':'Get-CimInstance Win32_Process | Select ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine,CreationDate',
 'services':'Get-CimInstance Win32_Service | Select Name,State,StartMode,StartName,PathName',
 'drivers':'Get-CimInstance Win32_SystemDriver | Select Name,State,StartMode,PathName',
 'signed_drivers':'Get-CimInstance Win32_PnPSignedDriver | Select DeviceName,DriverVersion,InfName,IsSigned,Signer',
 'tasks':'Get-ScheduledTask | Select TaskName,TaskPath,State,Actions,Triggers,Principal',
 'startup':'Get-CimInstance Win32_StartupCommand',
 'certificates':r'Get-ChildItem Cert:\CurrentUser,Cert:\LocalMachine -Recurse | Where-Object {$_ -is [System.Security.Cryptography.X509Certificates.X509Certificate2]} | Select PSParentPath,Subject,Issuer,Thumbprint,NotBefore,NotAfter,HasPrivateKey',
 'connections':'Get-NetTCPConnection',
 'dns':'Get-DnsClientServerAddress',
 'detections':'Get-MpThreatDetection',
 'bitlocker':'Get-BitLockerVolume | Select MountPoint,VolumeStatus,ProtectionStatus,EncryptionMethod,EncryptionPercentage',
 'users':'Get-LocalUser | Select Name,Enabled,LastLogon,SID',
 }
 for name,query in ps.items(): run(case,name,['powershell.exe','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+query+' | ConvertTo-Json -Depth 8'])
 for name,argv in {'ipconfig':['ipconfig','/all'],'routes':['route','print'],'dns_cache':['ipconfig','/displaydns'],'proxy':['netsh','winhttp','show','proxy'],'audit_policy':['auditpol','/get','/category:*']}.items(): run(case,name,argv)
 channels=['Security','System','Application','Microsoft-Windows-BitLocker-API/Management','Microsoft-Windows-BitLocker-API/Operational','Microsoft-Windows-CodeIntegrity/Operational','Microsoft-Windows-Windows Defender/Operational','Microsoft-Windows-PowerShell/Operational']
 (case/'evtx').mkdir(exist_ok=True)
 for i,ch in enumerate(channels): run(case,'evtx_'+str(i),['wevtutil','epl',ch,str((case/'evtx'/f'{i}.evtx').resolve()),'/ow:false'])
 save(case/'evtx'/'channels.json',dict(enumerate(channels)))
 # A bounded parsed view; originals above remain primary evidence.
 q="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624,4625,4688,4697,1102} -MaxEvents 5000 | ForEach-Object { [pscustomobject]@{time=$_.TimeCreated.ToUniversalTime().ToString('o'); event_id=$_.Id; record_id=$_.RecordId; xml=$_.ToXml()} } | ConvertTo-Json -Depth 5"
 run(case,'security_parsed',['powershell.exe','-NoProfile','-NonInteractive','-Command',q])

def android(case,serial,bugreport):
 adb=shutil.which('adb')
 if not adb: raise ValueError('Install reviewed Android platform tools separately; adb absent')
 p=[adb,'-s',serial]
 cmds={'version':['getprop'],'packages':['pm','list','packages','-f','-i'],'accessibility':['settings','get','secure','enabled_accessibility_services'],'keyboard':['settings','get','secure','default_input_method'],'policy':['dumpsys','device_policy'],'connectivity':['dumpsys','connectivity']}
 for n,c in cmds.items(): run(case,'android_'+n,p+['shell']+c)
 if bugreport: run(case,'android_bugreport',p+['bugreport',str((case/'bugreport.zip').resolve())],1200)

def import_file(case,source):
 src=Path(source).resolve(strict=True)
 if not src.is_file() or src.is_relative_to(case.resolve()): raise ValueError('External regular file required')
 before=src.stat(); h=digest(src); dst=case/'imports'/(h[:16]+'_'+src.name)
 dst.parent.mkdir(exist_ok=True)
 if dst.exists(): raise ValueError('Duplicate import')
 shutil.copy2(src,dst);after=src.stat()
 record(case,'import',source=str(src),destination=str(dst.relative_to(case)),source_hash=h,copy_hash=digest(dst),source_mtime_ns=before.st_mtime_ns,source_changed=(before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns))

def api(case,provider,application,user):
 token=os.environ.get('DFIR_ACCESS_TOKEN')
 if not token: raise ValueError('Set short-lived, authorized DFIR_ACCESS_TOKEN; token never saved')
 if provider=='entra':
  url='https://graph.microsoft.com/v1.0/auditLogs/signIns?$top=100'; hosts={'graph.microsoft.com'}
 else:
  if application not in ('login','admin','token','drive'): raise ValueError('Unsupported Workspace report application')
  url='https://admin.googleapis.com/admin/reports/v1/activity/users/'+urllib.parse.quote(user,safe='')+'/applications/'+application+'?maxResults=100';hosts={'admin.googleapis.com','www.googleapis.com'}
 # Prevent redirect-based Authorization disclosure.
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*a,**k): return None
 opener=urllib.request.build_opener(NoRedirect)
 folder=case/'api'/provider;folder.mkdir(parents=True,exist_ok=False)
 for page in range(100):
  parsed=urllib.parse.urlparse(url)
  if parsed.scheme!='https' or parsed.hostname not in hosts or parsed.username or parsed.password: raise ValueError('Untrusted pagination URL')
  req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
  with opener.open(req,timeout=60) as response: body=response.read(32*1024*1024+1)
  if len(body)>32*1024*1024: raise ValueError('Page too large')
  (folder/f'{page:04}.json').write_bytes(body);data=json.loads(body)
  record(case,'api_page',provider=provider,page=page,retrieved=now())
  if provider=='entra': nxt=data.get('@odata.nextLink')
  else:
   page_token=data.get('nextPageToken');nxt=(url.split('&pageToken=')[0]+'&pageToken='+urllib.parse.quote(page_token,safe='')) if page_token else None
  if not nxt: return
  url=nxt
 raise ValueError('Pagination capped at 100 pages; collection incomplete')

def normalize(row):
 original=str(row.get('time',''));uncertainty=row.get('uncertainty_seconds','unknown'); value=None;warning=None
 try:
  t=dt.datetime.fromisoformat(original.replace('Z','+00:00'))
  if t.tzinfo is None: warning='Timezone absent: UTC not inferred'
  else: value=t.astimezone(dt.timezone.utc).isoformat()
 except ValueError: warning='Unparsed timestamp'
 return dict(time_original=original,time_utc=value,uncertainty_seconds=uncertainty,clock_offset_seconds=row.get('clock_offset_seconds','unknown'),source=row.get('source',''),event_id=str(row.get('event_id','')),record_id=str(row.get('record_id','')),description=row.get('description',''),warning=warning)

def analyze(case,source):
 # Canonical CSV is explicit; no guessed mappings or automatic source attribution.
 with open(source,newline='',encoding='utf-8-sig') as f: events=[normalize(r) for r in csv.DictReader(f)]
 events.sort(key=lambda x:(x['time_utc'] is None,x['time_utc'] or ''))
 save(case/'analysis'/'timeline.json',events)
 findings=[]
 rules={'1102':('LOG_CLEARED','Security audit log cleared; maintenance is an alternative.'),'4697':('SERVICE_INSTALLED','Service installation; legitimate software installation is an alternative.')}
 for e in events:
  if e['event_id'] in rules:
   rule,explanation=rules[e['event_id']];findings.append(dict(rule=rule,assessment='review_required',evidence=e,explanation=explanation,conclusion='Not a compromise verdict'))
 save(case/'analysis'/'findings.json',findings)
 record(case,'analysis',source=str(Path(source).resolve()),source_sha256=digest(source),events=len(events),findings=len(findings))

def crypto(args):
 if args.action=='encrypt':
  age=shutil.which('age')
  if not age: raise ValueError('Reviewed age executable required')
  if Path(args.output).exists(): raise ValueError('Output exists')
  subprocess.run([age,'-r',args.recipient,'-o',args.output,args.input],check=True)
 elif args.action=='sign':
  subprocess.run(['openssl','dgst','-sha256','-sign',args.key,'-out',args.signature,args.input],check=True)
 else:
  subprocess.run(['openssl','dgst','-sha256','-verify',args.key,'-signature',args.signature,args.input],check=True)

def main():
 p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
 i=sub.add_parser('init');i.add_argument('case');i.add_argument('--collector',required=True);i.add_argument('--consent',action='store_true',required=True)
 for cmd in ['windows','android','import','api','analyze','seal','verify']:
  q=sub.add_parser(cmd);q.add_argument('case')
  if cmd=='android': q.add_argument('--serial',required=True);q.add_argument('--bugreport',action='store_true')
  if cmd=='import': q.add_argument('files',nargs='+')
  if cmd=='api': q.add_argument('--provider',choices=['entra','workspace'],required=True);q.add_argument('--application',default='login');q.add_argument('--user',default='all');q.add_argument('--consent',required=True,action='store_true')
  if cmd=='analyze':q.add_argument('csv')
 q=sub.add_parser('crypto');q.add_argument('action',choices=['encrypt','sign','verify-signature']);q.add_argument('--input',required=True);q.add_argument('--output');q.add_argument('--recipient');q.add_argument('--key');q.add_argument('--signature')
 a=p.parse_args()
 if a.cmd=='crypto':crypto(a);return
 case=Path(a.case).resolve()
 if a.cmd=='init':
  case.mkdir(parents=True,exist_ok=False)
  if os.name!='nt':os.chmod(case,0o700)
  save(case/'case.json',dict(collector=a.collector,created=now(),host=platform.node(),version='0.2.0-prototype',authorization_asserted=True))
  record(case,'init');manifest(case);return
 if not (case/'case.json').is_file():raise ValueError('Initialize case first')
 if a.cmd=='verify':sys.exit(0 if verify(case) else 1)
 if a.cmd=='seal':record(case,'seal');manifest(case);return
 # Never silently replace a previously sealed baseline before checking it.
 if not verify(case):raise ValueError('Integrity mismatch; preserve case and investigate before further writes')
 try:
  if a.cmd=='windows':collect_windows(case)
  elif a.cmd=='android':android(case,a.serial,a.bugreport)
  elif a.cmd=='import':
   for f in a.files:import_file(case,f)
  elif a.cmd=='api':api(case,a.provider,a.application,a.user)
  elif a.cmd=='analyze':analyze(case,a.csv)
 except Exception as e:
  record(case,'failure',module=a.cmd,error=type(e).__name__+': '+str(e));raise
 finally:manifest(case)
if __name__=='__main__':main()
