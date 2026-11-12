"""Synthetic private ZIP/reconciliation checks; never real buyer or owner acceptance."""
from __future__ import annotations
import hashlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.build_private_customer_candidate import create_private_candidate
from scripts.link_private_candidate_evidence import link_candidate_evidence,main
from scripts.windows_acceptance_contract import FORMAT as READONLY_FORMAT, PENDING as READONLY_PENDING
from scripts.windows_local_exe_smoke_contract import FORMAT as SMOKE_FORMAT, PENDING as SMOKE_PENDING

class BindingTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory(prefix='codechecker-link-synth-');self.addCleanup(t.cleanup)
  self.root=Path(t.name);self.exe=self.root/'CodeCheckerOffline.exe';self.exe.write_bytes(b'MZ PURE SYNTHETIC NOT EXECUTABLE')
  docs=[]
  for i,name in enumerate(['README.txt','LICENSE','NOTICE.txt','component.txt']):
   f=self.root/('source-'+name);f.write_text('SYNTHETIC NONLICENSE '+str(i));docs.append(f)
  self.zip=self.root/'candidate.zip';create_private_candidate(exe=self.exe,readme=docs[0],license_file=docs[1],notice=docs[2],component_licenses={'example.txt':docs[3]},output=self.zip)
  self.sha=hashlib.sha256(self.exe.read_bytes()).hexdigest()
  size=self.exe.stat().st_size
  self.readonly=dict(format=READONLY_FORMAT,collection_method='win32_readonly_powershell',
    scope='local_binary_only',exe_sha256=self.sha,exe_bytes=size,
    signature_observation='Unavailable',
    defender=dict(availability='UNVERIFIED',antivirus_enabled=None,real_time_protection_enabled=None),
    pending_gates={key:'UNVERIFIED' for key in READONLY_PENDING},
    customer_release_ready=False,legal_notice_approved=False)
  self.smoke=dict(format=SMOKE_FORMAT,collection_method='two_synthetic_exe_modes_no_python_required',
    scope='existing_local_exe_only',exe_sha256=self.sha,exe_bytes=size,
    observed_synthetic=dict(packaged_tk_gui_startup='PASS',packaged_preview_scan_report='PASS',
    executable_hash_stable=True),pending_gates={key:'UNVERIFIED' for key in SMOKE_PENDING},
    actual_customer_code_used=False,actual_customer_release_ready=False,legal_notice_approved=False)

 def test_same_exe_receipts_linked_but_no_release(self):
  r=link_candidate_evidence(self.exe,self.zip,self.readonly,self.smoke)
  self.assertEqual(r['status'],'PRIVATE_ZIP_AND_WINDOWS_RECEIPTS_LINKED_RELEASE_BLOCKED')
  self.assertEqual(r['exact_exe_sha256'],self.sha)
  self.assertEqual(r['entries_checked'],6)
  self.assertFalse(r['customer_release_ready'])
  self.assertTrue(all(x=='UNVERIFIED' for x in r['human_release_gates'].values()))
  self.assertNotIn(str(self.root),json.dumps(r))

 def test_distinct_same_length_binary_mismatch_rejected(self):
  self.exe.write_bytes(b'Mz PURE SYNTHETIC NOT EXECUTABLE')
  with self.assertRaises(Exception):link_candidate_evidence(self.exe,self.zip,self.readonly,self.smoke)

 def test_mismatched_receipt_exe_sha_rejected(self):
  altered=dict(self.smoke,exe_sha256='0'*64)
  with self.assertRaises(Exception):link_candidate_evidence(self.exe,self.zip,self.readonly,altered)

 def test_forged_binary_release_status_rejected(self):
  from scripts import link_private_candidate_evidence as mod
  original=mod.inspect_candidate(self.zip,self.exe)
  for update in ({'customer_release_ready':True},{'owner_release_approval':True},{'status':'PUBLISHED'}):
   forged=dict(original,**update)
   with patch.object(mod,'inspect_candidate',return_value=forged):
    with self.assertRaises(ValueError):mod.link_candidate_evidence(self.exe,self.zip,self.readonly,self.smoke)

 def test_forged_windows_human_gates_rejected(self):
  from scripts import link_private_candidate_evidence as mod
  normal=mod.consolidate(self.exe,self.readonly,self.smoke)
  forged=dict(normal,human_release_gates={**normal['human_release_gates'],'defender_on_buyer_pc':'PASS'})
  with patch.object(mod,'consolidate',return_value=forged):
   with self.assertRaises(ValueError):mod.link_candidate_evidence(self.exe,self.zip,self.readonly,self.smoke)

 def test_changed_zip_after_receipt_integration_detected(self):
  from scripts import link_private_candidate_evidence as mod
  original=mod.inspect_candidate(self.zip,self.exe)
  changed=dict(original,candidate_zip_sha256='0'*64)
  with patch.object(mod,'inspect_candidate',side_effect=[original,changed]):
   with self.assertRaises(ValueError):mod.link_candidate_evidence(self.exe,self.zip,self.readonly,self.smoke)

 def test_cli_evidence_file_new_and_blocked(self):
  ro=self.root/'readonly.json';sm=self.root/'smoke.json';out=self.root/'binding.json'
  ro.write_text(json.dumps(self.readonly));sm.write_text(json.dumps(self.smoke))
  argv=['--exe',str(self.exe),'--zip',str(self.zip),'--readonly',str(ro),'--smoke',str(sm),'--out',str(out)]
  with patch('sys.stdout',new_callable=io.StringIO) as stdout:
   self.assertEqual(main(argv),0);self.assertNotIn(str(self.root),stdout.getvalue())
  data=json.loads(out.read_text());self.assertFalse(data['customer_release_ready'])
  with patch('sys.stdout',new_callable=io.StringIO):self.assertEqual(main(argv),1)

 def test_cli_refuses_reused_source_or_relative_output(self):
  ro=self.root/'ro.json';sm=self.root/'sm.json';ro.write_text(json.dumps(self.readonly));sm.write_text(json.dumps(self.smoke))
  argv=['--exe',str(self.exe),'--zip',str(self.zip),'--readonly',str(ro),'--smoke',str(sm),'--out','relative.json']
  with patch('sys.stdout',new_callable=io.StringIO):self.assertEqual(main(argv),1)
  argv[-1]=str(ro)
  with patch('sys.stdout',new_callable=io.StringIO):self.assertEqual(main(argv),1)

if __name__=='__main__':unittest.main()
