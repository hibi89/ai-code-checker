"""Synthetic-only exact DLL provenance tests; never execute candidate binaries."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.runtime_version_receipt import capture_receipt
from scripts.verify_frozen_tcltk_dll_provenance import verify_dlls

class FakeTk:
    def __init__(self): self.tk = self
    def withdraw(self): pass
    def call(self, *args): return "8.6.15"
    def destroy(self): pass

class FakeArchive:
    def __init__(self, content):
        self.toc = {k: (0, 0, len(v), 0, "b") for k,v in content.items()}
        self.content = content
    def extract(self, name): return self.content[name]

class DllProvenanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.exe = self.folder/"inert.exe"
        self.exe.write_bytes(b"MZ synthetic EXE with no executable instructions")
        self.data = {"tcl86t.dll":b"SYNTHETIC Tcl", "tk86t.dll":b"SYNTHETIC Tk"}
        self.toc=[]
        for name, raw in self.data.items():
            file=self.folder/name
            file.write_bytes(raw)
            self.toc.append((name,file,"BINARY"))
        self.reader=FakeArchive(self.data.copy())
        self.audit={"exe_sha256":hashlib.sha256(self.exe.read_bytes()).hexdigest(),
                    "exe_bytes":self.exe.stat().st_size,
                    "archive":{"top_level":[{"name":x} for x in self.data]},
                    "customer_release_ready":False,
                    "license_compliance_certified":False,
                    "third_party_notice_ready_to_distribute":False}
        self.receipt=capture_receipt(self.exe,FakeTk,frozen=True,python_version="3.13.9")
    def verify(self):
        return verify_dlls(self.exe,self.audit,self.receipt,self.toc,self.reader)
    def test_exact_bundled_dll_match_but_never_vendor_or_release_approval(self):
        r=self.verify()
        self.assertEqual([x["role"] for x in r["dlls"]],["tcl","tk"])
        self.assertTrue(r["exact_embedded_build_source_bytes_match"])
        self.assertFalse(r["vendor_binary_ownership_verified"])
        self.assertFalse(r["customer_release_ready"])
        self.assertNotIn(str(self.folder),str(r))
    def test_embedded_modified_bytes_rejected(self):
        self.reader.content["tcl86t.dll"]=b"changed"
        with self.assertRaises(ValueError):self.verify()
    def test_same_size_changed_exe_rejected(self):
        self.exe.write_bytes(self.exe.read_bytes().replace(b"synthetic",b"synTHEtic"))
        with self.assertRaises(ValueError):self.verify()
    def test_missing_tk_dll_and_ambiguous_tcl_dll_rejected(self):
        self.reader.toc.pop("tk86t.dll")
        with self.assertRaises(ValueError):self.verify()
        self.reader=FakeArchive(self.data.copy())
        self.reader.toc["tcl87t.dll"]=(0,0,1,0,"b")
        self.audit["archive"]["top_level"].append({"name":"tcl87t.dll"})
        with self.assertRaises(ValueError):self.verify()
    def test_missing_duplicate_or_wrong_type_build_source_rejected(self):
        self.toc.append(self.toc[0])
        with self.assertRaises(ValueError):self.verify()
        self.toc.pop()
        self.toc[0]=(self.toc[0][0],self.toc[0][1],"DATA")
        with self.assertRaises(ValueError):self.verify()
    def test_installed_build_source_changed_or_linked_rejected(self):
        p=self.folder/"tcl86t.dll"
        p.write_bytes(b"CHANGED")
        with self.assertRaises(ValueError):self.verify()
        p.unlink()
        try:p.symlink_to(self.folder/"tk86t.dll")
        except (OSError,NotImplementedError):self.skipTest("Symlink unavailable")
        with self.assertRaises(ValueError):self.verify()
    def test_forged_release_or_wrong_runtime_receipt_rejected(self):
        self.audit["customer_release_ready"]=True
        with self.assertRaises(ValueError):self.verify()
        self.audit["customer_release_ready"]=False
        self.receipt["exe_sha256"]="0"*64
        with self.assertRaises(ValueError):self.verify()
    def test_missing_archive_entry_or_wrong_size_rejected(self):
        self.audit["archive"]["top_level"].pop()
        with self.assertRaises(ValueError):self.verify()
        self.audit["archive"]["top_level"].append({"name":"tk86t.dll"})
        self.audit["exe_bytes"]+=1
        with self.assertRaises(ValueError):self.verify()

if __name__=="__main__":unittest.main()
