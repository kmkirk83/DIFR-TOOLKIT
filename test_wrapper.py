import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ast
source=Path(__file__).resolve().parents[1]/'dfir_workbench.py'
tree=ast.parse(source.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='App')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
# Exercise the actual path-validation method without importing unavailable Tk.
module=ast.Module(body=[ast.ClassDef(name='App',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[])
namespace={'Path':Path};exec(compile(ast.fix_missing_locations(module),str(source),'exec'),namespace)
App=namespace['App']
class Var:
 def __init__(self,v):self.v=v
 def get(self):return self.v
class Validation(unittest.TestCase):
 def fixture(self,folder):
  app=object.__new__(App);tool=folder/'dfir_kit.py';tool.write_text('# fixture only')
  app.tool=Var(str(tool));app.case=Var(str(folder/'case'));return app
 def test_existing_case(self):
  with tempfile.TemporaryDirectory() as d:
   app=self.fixture(Path(d));c=Path(app.case.get());c.mkdir();(c/'case.json').write_text('{}')
   self.assertEqual(app.validate()[1],c.resolve())
 def test_uninitialized_case_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   app=self.fixture(Path(d))
   with self.assertRaises(ValueError):app.validate()
 def test_new_path_allowed(self):
  with tempfile.TemporaryDirectory() as d:
   app=self.fixture(Path(d));self.assertEqual(app.validate(False)[1],Path(app.case.get()).resolve())
 def test_missing_tool_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   app=self.fixture(Path(d));app.tool=Var('')
   with self.assertRaises(ValueError):app.validate(False)
 def test_empty_case_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   app=self.fixture(Path(d));app.case=Var('')
   with self.assertRaises(ValueError):app.validate(False)
