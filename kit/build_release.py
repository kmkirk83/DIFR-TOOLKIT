from pathlib import Path
import zipfile,hashlib
root=Path(__file__).resolve().parent
out=root/'dist';out.mkdir(exist_ok=True)
path=out/'dfir-kit-source.zip'
with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_STORED) as z:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or any(x in p.relative_to(root).parts for x in ('dist','__pycache__','.git')):continue
  i=zipfile.ZipInfo(p.relative_to(root).as_posix(),date_time=(2020,1,1,0,0,0));i.external_attr=0o100644<<16
  z.writestr(i,p.read_bytes())
print(hashlib.sha256(path.read_bytes()).hexdigest())
