#!/usr/bin/env python3
"""DFIR Workbench: standard-library desktop wrapper for DFIR Kit 0.2."""
import datetime, json, os, platform, queue, shlex, shutil, subprocess, sys, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BG='#101827'; PANEL='#182438'; TEXT='#e6edf7'; MUTED='#a9bad1'; ACCENT='#56c9be'

class Tip:
 def __init__(self, widget, text):
  self.widget=widget;self.text=text;self.window=None;self.timer=None
  widget.bind('<Enter>',self.enter,add='+');widget.bind('<Leave>',self.leave,add='+');widget.bind('<ButtonPress>',self.leave,add='+')
 def enter(self,event=None): self.timer=self.widget.after(550,self.show)
 def leave(self,event=None):
  if self.timer:
   try:self.widget.after_cancel(self.timer)
   except tk.TclError:pass
   self.timer=None
  if self.window:self.window.destroy();self.window=None
 def show(self):
  self.window=tk.Toplevel(self.widget);self.window.wm_overrideredirect(True)
  self.window.geometry('+%d+%d'%(self.widget.winfo_rootx()+15,self.widget.winfo_rooty()+self.widget.winfo_height()+6))
  tk.Label(self.window,text=self.text,bg='#263a52',fg=TEXT,justify='left',wraplength=390,padx=12,pady=9).pack()

class App:
 def __init__(self,root):
  self.root=root;root.title('DFIR Workbench · Evidence first');root.geometry('1180x850');root.minsize(950,720);root.configure(bg=BG)
  self.events=queue.Queue();self.process=None;self.busy=False;self.closing=False
  self.tool=tk.StringVar(value=str(Path(__file__).with_name('dfir_kit.py')) if Path(__file__).with_name('dfir_kit.py').exists() else '')
  self.case=tk.StringVar();self.collector=tk.StringVar();self.status=tk.StringVar(value='Ready · Select your toolkit and case')
  self.provider=tk.StringVar(value='entra');self.application=tk.StringVar(value='login');self.user=tk.StringVar(value='all');self.serial=tk.StringVar();self.bug=tk.BooleanVar();self.consent=tk.BooleanVar();self.reduce=tk.BooleanVar()
  self.csv=tk.StringVar();self.crypto_action=tk.StringVar(value='encrypt');self.crypto_input=tk.StringVar();self.crypto_output=tk.StringVar();self.crypto_key=tk.StringVar();self.crypto_sig=tk.StringVar();self.recipient=tk.StringVar()
  self.files=[];self.make_style();self.make_menu();self.make_ui();self.refresh_checks();self.root.after(100,self.poll);root.protocol('WM_DELETE_WINDOW',self.close)
 def make_style(self):
  s=ttk.Style();s.theme_use('clam');s.configure('.',background=BG,foreground=TEXT,font=('Segoe UI',10))
  s.configure('TFrame',background=BG);s.configure('Card.TFrame',background=PANEL)
  s.configure('TLabel',background=BG,foreground=TEXT);s.configure('Muted.TLabel',foreground=MUTED)
  s.configure('Title.TLabel',font=('Segoe UI',24,'bold'));s.configure('Heading.TLabel',font=('Segoe UI',13,'bold'))
  s.configure('TButton',background='#263c55',foreground=TEXT,padding=(12,9),borderwidth=0)
  s.map('TButton',background=[('active','#355675'),('disabled','#202c3d')],foreground=[('disabled','#718096')])
  s.configure('Accent.TButton',background='#227b75');s.map('Accent.TButton',background=[('active','#29978e')])
  s.configure('TEntry',fieldbackground='#213149',foreground=TEXT,insertcolor=TEXT,padding=7)
  s.configure('TCombobox',fieldbackground='#213149',background='#263c55',foreground=TEXT,padding=6)
  s.map('TCombobox',fieldbackground=[('readonly','#213149')],foreground=[('readonly',TEXT)])
  s.configure('TNotebook',background=BG,borderwidth=0);s.configure('TNotebook.Tab',background=PANEL,padding=(14,10));s.map('TNotebook.Tab',background=[('selected','#29445d')])
  s.configure('TCheckbutton',background=BG,foreground=TEXT);s.map('TCheckbutton',background=[('active',BG)])
  s.configure('Horizontal.TProgressbar',background=ACCENT,troughcolor=PANEL,borderwidth=0)
 def make_menu(self):
  menu=tk.Menu(self.root)
  case=tk.Menu(menu,tearoff=False);case.add_command(label='Select toolkit…',command=self.select_tool);case.add_command(label='Open existing case…',command=self.open_case);case.add_command(label='Create new case…',command=lambda:self.tabs.select(self.setup_tab));case.add_separator();case.add_command(label='Open case folder',command=self.open_folder);case.add_command(label='Exit',command=self.close);menu.add_cascade(label='Case',menu=case)
  tools=tk.Menu(menu,tearoff=False);tools.add_command(label='Refresh prerequisites',command=self.refresh_checks);tools.add_command(label='Verify current case',command=lambda:self.launch_case('verify'));tools.add_command(label='Export session log…',command=self.export_log);menu.add_cascade(label='Tools',menu=tools)
  view=tk.Menu(menu,tearoff=False);view.add_checkbutton(label='Reduce motion',variable=self.reduce,command=self.motion_changed);menu.add_cascade(label='View',menu=view)
  helpmenu=tk.Menu(menu,tearoff=False);helpmenu.add_command(label='Safety & limitations',command=self.help);helpmenu.add_command(label='About',command=lambda:messagebox.showinfo('About','DFIR Workbench 0.1\nLocal desktop wrapper for DFIR Kit 0.2.\nNo telemetry. No automatic compromise verdict.\nGUI not tested on Windows/macOS desktops.'));menu.add_cascade(label='Help',menu=helpmenu);self.root.config(menu=menu)
 def button(self,parent,text,command,tip='',accent=False):
  b=ttk.Button(parent,text=text,command=command,style='Accent.TButton' if accent else 'TButton');b.pack(side='left',padx=(0,8),pady=6)
  if tip:Tip(b,tip)
  return b
 def row(self,parent,label,var,browse=None,tip=''):
  f=ttk.Frame(parent);f.pack(fill='x',pady=5);ttk.Label(f,text=label,width=19).pack(side='left');e=ttk.Entry(f,textvariable=var);e.pack(side='left',fill='x',expand=True)
  if browse:self.button(f,'Browse…',browse)
  if tip:Tip(e,tip)
  return e
 def note(self,parent,text):ttk.Label(parent,text=text,style='Muted.TLabel',wraplength=970,justify='left').pack(anchor='w',pady=(2,10))
 def tab(self,name):
  f=ttk.Frame(self.tabs,padding=18);self.tabs.add(f,text=name);return f
 def actions(self,parent):
  f=ttk.Frame(parent);f.pack(fill='x',pady=4);return f
 def make_ui(self):
  head=ttk.Frame(self.root,padding=(24,18));head.pack(fill='x');ttk.Label(head,text='DFIR Workbench',style='Title.TLabel').pack(anchor='w');ttk.Label(head,text='Collect carefully. Preserve context. Review before concluding.',style='Muted.TLabel').pack(anchor='w',pady=(3,0))
  paths=ttk.Frame(self.root,padding=(24,0));paths.pack(fill='x');self.row(paths,'Toolkit script',self.tool,self.select_tool,'Select the dfir_kit.py from DFIR Kit 0.2. Selecting is safe; running executes this Python script.');self.row(paths,'Active case',self.case,self.open_case,'Existing case directory containing case.json, or a new empty path for initialization.')
  self.tabs=ttk.Notebook(self.root);self.tabs.pack(fill='both',expand=True,padx=24,pady=10)
  self.setup_tab=self.tab('Case');self.note(self.setup_tab,'Start with a protected destination. The wrapper does not establish forensic validity or make a device trustworthy.')
  self.row(self.setup_tab,'Collector',self.collector);ttk.Checkbutton(self.setup_tab,text='I own these devices/accounts or have explicit permission to examine them.',variable=self.consent).pack(anchor='w',pady=8)
  f=self.actions(self.setup_tab);self.button(f,'Choose new case path',self.new_path);self.button(f,'Initialize case',self.initialize,accent=True);self.button(f,'Verify integrity',lambda:self.launch_case('verify'),'Checks the current local manifest; not source authenticity.');self.button(f,'Open case folder',self.open_folder)
  ttk.Label(self.setup_tab,text='Prerequisites',style='Heading.TLabel').pack(anchor='w',pady=(15,6));self.checks=tk.Text(self.setup_tab,height=6,bg=PANEL,fg=MUTED,relief='flat',font=('Consolas',10),state='disabled');self.checks.pack(fill='x');self.button(self.actions(self.setup_tab),'Refresh checks',self.refresh_checks)
  c=self.tab('Collection');self.note(c,'Commands run locally in a background process. Windows collection may need an elevated terminal. Android requires reviewed ADB and prior device authorization.')
  self.button(self.actions(c),'Collect Windows evidence',lambda:self.launch_case('windows',confirm='Run live Windows collection? It executes commands and writes evidence files.'),accent=True)
  self.row(c,'ADB device serial',self.serial,tip='Use the exact serial shown by adb devices. No discovery or device authorization is performed automatically.')
  ttk.Checkbutton(c,text='Include Android bugreport (sensitive; may take several minutes)',variable=self.bug).pack(anchor='w',pady=6)
  f=self.actions(c);self.button(f,'List ADB devices',self.adb_devices);self.button(f,'Collect Android evidence',self.collect_android,accent=True)
  a=self.tab('Account APIs');self.note(a,'Enterprise API adapters only. OAuth login is not included. Set DFIR_ACCESS_TOKEN in the environment before starting the app; it is passed to the child process, not displayed or saved here. Personal account coverage is not implied.')
  f=self.actions(a);ttk.Label(f,text='Provider',width=19).pack(side='left');cb=ttk.Combobox(f,textvariable=self.provider,values=['entra','workspace'],state='readonly');cb.pack(side='left');cb.bind('<<ComboboxSelected>>',lambda e:self.provider_changed())
  f=self.actions(a);ttk.Label(f,text='Workspace report',width=19).pack(side='left');self.report_combo=ttk.Combobox(f,textvariable=self.application,values=['login','admin','token','drive'],state='readonly');self.report_combo.pack(side='left')
  self.apiuser=self.row(a,'Workspace user',self.user,tip='Use all or an authorized user identifier. Only applicable to Workspace.')
  self.button(self.actions(a),'Collect authorized API records',self.collect_api,accent=True);self.provider_changed()
  i=self.tab('Import & timeline');self.note(i,'Import original files without opening them. Timeline analysis requires canonical CSV columns; this wrapper does not turn arbitrary exports into a normalized timeline.')
  f=self.actions(i);self.button(f,'Add evidence files…',self.add_files);self.button(f,'Remove selected',self.remove_files);self.button(f,'Import selected files',self.import_files,accent=True)
  self.filelist=tk.Listbox(i,height=4,bg=PANEL,fg=TEXT,selectbackground='#355675',selectmode='extended',relief='flat');self.filelist.pack(fill='x',pady=5)
  self.row(i,'Canonical events CSV',self.csv,lambda:self.pick(self.csv));f=self.actions(i);self.button(f,'Analyze timeline',self.analyze,accent=True);self.button(f,'View findings',lambda:self.view_json('analysis/findings.json'));self.button(f,'View timeline',lambda:self.view_json('analysis/timeline.json'))
  s=self.tab('Protection');self.note(s,'External age/OpenSSL required. Encryption takes a prepared archive, not a directory. Plaintext remains. Signing keys must be managed separately. No keys are generated or stored by this wrapper.')
  f=self.actions(s);ttk.Label(f,text='Operation',width=19).pack(side='left');ttk.Combobox(f,textvariable=self.crypto_action,values=['encrypt','sign','verify-signature'],state='readonly').pack(side='left')
  self.row(s,'Input file',self.crypto_input,lambda:self.pick(self.crypto_input));self.row(s,'Encrypted output',self.crypto_output,lambda:self.pick(self.crypto_output,True));self.row(s,'age recipient',self.recipient,tip='Public age recipient, never a private key.');self.row(s,'Signing / verify key',self.crypto_key,lambda:self.pick(self.crypto_key));self.row(s,'Signature file',self.crypto_sig,lambda:self.pick(self.crypto_sig,self.crypto_action.get()=='sign'))
  self.button(self.actions(s),'Run protection operation',self.protect,accent=True)
  bottom=ttk.Frame(self.root,padding=(24,0,24,14));bottom.pack(fill='x');self.progress=ttk.Progressbar(bottom,mode='indeterminate');self.progress.pack(fill='x',pady=(0,6));f=ttk.Frame(bottom);f.pack(fill='x');ttk.Label(f,textvariable=self.status,style='Muted.TLabel').pack(side='left');ttk.Button(f,text='Export log',command=self.export_log).pack(side='right');self.stopbutton=ttk.Button(f,text='Stop process…',command=self.stop,state='disabled');self.stopbutton.pack(side='right',padx=8)
  box=ttk.Frame(bottom);box.pack(fill='x',pady=(8,0));self.log=tk.Text(box,height=7,bg='#0a111d',fg='#b5d1d9',font=('Consolas',9),relief='flat',wrap='word',state='disabled');self.log.pack(side='left',fill='both',expand=True);scroll=ttk.Scrollbar(box,command=self.log.yview);scroll.pack(side='right',fill='y');self.log.configure(yscrollcommand=scroll.set)
 def pick(self,var,save=False):
  path=filedialog.asksaveasfilename() if save else filedialog.askopenfilename()
  if path:var.set(path)
 def select_tool(self):self.pick(self.tool)
 def open_case(self):
  p=filedialog.askdirectory()
  if p:self.case.set(p)
 def new_path(self):
  p=filedialog.asksaveasfilename(title='Choose a NEW case directory name',confirmoverwrite=True)
  if p:self.case.set(p)
 def refresh_checks(self):
  checks=['Python: '+sys.version.split()[0]+' · '+platform.system()]
  for name in ['adb','age','openssl']:checks.append(name+': '+(shutil.which(name) or 'Not found — optional external dependency'))
  checks.append('API token: '+('Present in environment' if os.environ.get('DFIR_ACCESS_TOKEN') else 'Not present'))
  self.checks.configure(state='normal');self.checks.delete('1.0','end');self.checks.insert('end','\n'.join(checks));self.checks.configure(state='disabled')
 def provider_changed(self):
  state='readonly' if self.provider.get()=='workspace' else 'disabled';self.report_combo.configure(state=state);self.apiuser.configure(state='normal' if state=='readonly' else 'disabled')
 def validate(self,existing=True):
  p=Path(self.tool.get()).expanduser()
  if not self.tool.get() or not p.is_file():raise ValueError('Select the existing DFIR Kit 0.2 Python script.')
  if not self.case.get().strip():raise ValueError('Choose a case directory.')
  c=Path(self.case.get()).expanduser().resolve()
  if existing and not (c/'case.json').is_file():raise ValueError('Select an initialized case containing case.json.')
  return p.resolve(),c
 def launch_case(self,cmd,extra=None,confirm=None):
  try:
   p,c=self.validate()
   if not self.consent.get():raise ValueError('Confirm authorization in the Case tab before running toolkit commands.')
   if cmd=='windows' and sys.platform!='win32':raise ValueError('Windows collection requires Windows.')
   if confirm and not messagebox.askyesno('Confirm collection',confirm):return
   self.start([sys.executable,str(p),cmd,str(c)]+(extra or []),cmd,c)
  except Exception as e:messagebox.showerror('Cannot run',str(e))
 def initialize(self):
  try:
   p,c=self.validate(False)
   if c.exists():raise ValueError('Choose a new case path that does not already exist.')
   if not self.collector.get().strip() or not self.consent.get():raise ValueError('Enter collector name and confirm authorization.')
   if messagebox.askyesno('Initialize case','Create case at:\n'+str(c)+'\n\nThis runs the selected toolkit script. Only run source you trust.'):
    self.start([sys.executable,str(p),'init',str(c),'--collector',self.collector.get().strip(),'--consent'],'initialize',c)
  except Exception as e:messagebox.showerror('Cannot initialize',str(e))
 def collect_android(self):
  if not self.serial.get().strip():messagebox.showerror('Serial required','Enter an authorized ADB serial.');return
  args=['--serial',self.serial.get().strip()]+(['--bugreport'] if self.bug.get() else [])
  self.launch_case('android',args,'Collect from the authorized phone? Bugreports and device inventories can contain sensitive data.')
 def adb_devices(self):
  adb=shutil.which('adb')
  if not adb:messagebox.showerror('ADB absent','Install reviewed platform tools separately.');return
  self.start([adb,'devices'],'ADB devices',None)
 def collect_api(self):
  if not os.environ.get('DFIR_ACCESS_TOKEN'):messagebox.showerror('Token missing','Start the app from an environment containing your authorized DFIR_ACCESS_TOKEN.');return
  args=['--provider',self.provider.get(),'--consent']
  if self.provider.get()=='workspace':args+=['--application',self.application.get(),'--user',self.user.get().strip() or 'all']
  self.launch_case('api',args,'Request records from this provider using the token in your environment? This contacts an external service and collects sensitive records.')
 def add_files(self):
  for p in filedialog.askopenfilenames():
   if p not in self.files:self.files.append(p);self.filelist.insert('end',p)
 def remove_files(self):
  for i in reversed(self.filelist.curselection()):del self.files[i];self.filelist.delete(i)
 def import_files(self):
  if not self.files:messagebox.showinfo('No files','Add evidence files first.');return
  self.launch_case('import',self.files.copy(),'Copy these files into the case? Originals are not intentionally modified.')
 def analyze(self):
  if not Path(self.csv.get()).is_file():messagebox.showerror('CSV required','Select a canonical timeline CSV.');return
  self.launch_case('analyze',[str(Path(self.csv.get()).resolve())])
 def protect(self):
  try:
   p=Path(self.tool.get()).resolve()
   if not p.is_file():raise ValueError('Select toolkit script.')
   action=self.crypto_action.get();inp=Path(self.crypto_input.get())
   if not inp.is_file():raise ValueError('Choose an input file.')
   args=[sys.executable,str(p),'crypto',action,'--input',str(inp.resolve())]
   if action=='encrypt':
    if not shutil.which('age'):raise ValueError('age is not installed.')
    if not self.recipient.get().strip() or not self.crypto_output.get():raise ValueError('Recipient and output required.')
    if Path(self.crypto_output.get()).exists():raise ValueError('Choose an output that does not exist.')
    args+=['--recipient',self.recipient.get().strip(),'--output',self.crypto_output.get()]
   else:
    if not shutil.which('openssl'):raise ValueError('OpenSSL is not installed.')
    if not Path(self.crypto_key.get()).is_file() or not self.crypto_sig.get():raise ValueError('Choose key and signature paths.')
    if action=='sign' and Path(self.crypto_sig.get()).exists():raise ValueError('Signature output already exists.')
    if action=='verify-signature' and not Path(self.crypto_sig.get()).is_file():raise ValueError('Signature file not found.')
    args+=['--key',self.crypto_key.get(),'--signature',self.crypto_sig.get()]
   if messagebox.askyesno('Confirm protection operation','Run '+action+' on:\n'+str(inp)+'\n\nEncrypted private-key prompts are not supported by this GUI. Do not weaken key protection to use it. Use a trusted terminal instead when a passphrase is required.'):
    self.start(args,action,None)
  except Exception as e:messagebox.showerror('Cannot run protection',str(e))
 def start(self,argv,label,case):
  if self.busy:messagebox.showwarning('Operation running','Wait for the current operation or stop it first.');return
  self.busy=True;self.stopbutton.configure(state='normal');self.status.set('Running · '+label)
  if not self.reduce.get():self.progress.start(14)
  self.append('\n['+datetime.datetime.now().isoformat(timespec='seconds')+'] '+label+'\n'+shlex.join(argv)+'\n')
  def worker():
   started=time.monotonic();code=-1
   try:
    # No shell; input disabled to avoid hidden password prompts. Token never logged by wrapper.
    proc=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',bufsize=1)
    self.process=proc
    for line in proc.stdout:self.events.put(('line',line))
    code=proc.wait()
   except Exception as e:self.events.put(('line','Launch error: '+str(e)+'\n'))
   finally:self.events.put(('done',(code,label,time.monotonic()-started)))
  threading.Thread(target=worker,daemon=True).start()
 def poll(self):
  try:
   for _ in range(150):
    kind,payload=self.events.get_nowait()
    if kind=='line':self.append(payload)
    elif kind=='done':
     code,label,elapsed=payload;self.busy=False;self.process=None;self.progress.stop();self.progress['value']=0;self.stopbutton.configure(state='disabled');self.status.set(('Completed' if code==0 else 'Needs review')+' · '+label+f' · exit {code} · {elapsed:.1f}s');self.append(f'\nExit {code}. Success is not a compromise assessment.\n')
     if self.closing:self.root.destroy();return
  except queue.Empty:pass
  self.root.after(100,self.poll)
 def append(self,text):
  self.log.configure(state='normal');self.log.insert('end',text)
  if int(self.log.index('end-1c').split('.')[0])>4000:self.log.delete('1.0','1000.0')
  self.log.see('end');self.log.configure(state='disabled')
 def stop(self):
  if not self.busy:return
  if not messagebox.askyesno('Stop operation?','Stopping can leave incomplete evidence and an outdated manifest. Child collector processes may continue. Preserve partial output and review it before reuse.'):return
  p=self.process
  if p and p.poll() is None:
   try:p.terminate();self.status.set('Stopping · partial evidence may remain')
   except OSError as e:messagebox.showerror('Stop failed',str(e))
 def motion_changed(self):
  if self.reduce.get():self.progress.stop()
  elif self.busy:self.progress.start(14)
 def export_log(self):
  p=filedialog.asksaveasfilename(defaultextension='.txt',title='Export visible session log (may contain sensitive data)')
  if p:
   try:Path(p).write_text(self.log.get('1.0','end'),encoding='utf-8')
   except OSError as e:messagebox.showerror('Export failed',str(e))
 def open_folder(self):
  try:
   p=Path(self.case.get()).resolve()
   if not self.case.get() or not p.is_dir():raise ValueError('Select an existing case directory.')
   if sys.platform=='win32':os.startfile(str(p))
   else:subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',str(p)])
  except Exception as e:messagebox.showerror('Cannot open folder',str(e))
 def view_json(self,relative):
  try:
   _,c=self.validate();p=c/relative
   if not p.is_file():raise ValueError('No output yet. Run analysis first.')
   if p.stat().st_size>8*1024*1024:raise ValueError('File exceeds viewer limit. Use a trusted local viewer.')
   data=json.loads(p.read_text(encoding='utf-8'));w=tk.Toplevel(self.root);w.title(relative+' · review, not a verdict');w.geometry('900x600');t=tk.Text(w,bg=BG,fg=TEXT,wrap='word');t.pack(fill='both',expand=True);t.insert('1.0',json.dumps(data,indent=2));t.configure(state='disabled')
  except Exception as e:messagebox.showerror('Cannot view output',str(e))
 def help(self):messagebox.showinfo('Safety & limitations','Use only with permission.\n\nLive collection changes devices. This wrapper does not validate evidence or identify attackers. No disk imaging, RAM acquisition, voice classification or router control is added.\n\nRaw logs may contain secrets. Store cases on protected media. Sign and retain manifest snapshots independently. Never use a new baseline to hide an integrity mismatch.\n\nToolkit exit 0 means the command completed, not that every underlying collector succeeded. Review journal.jsonl.\n\nGUI logs are truncated to control memory; preserve original case records.')
 def close(self):
  if self.busy:
   messagebox.showwarning('Operation running','Finish or stop the operation before closing. Closing a collector can leave partial output.');return
  self.root.destroy()

if __name__=='__main__':
 root=tk.Tk();App(root);root.mainloop()
