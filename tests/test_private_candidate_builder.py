"""Synthetic inert binary and author-supplied placeholder texts; no real license approval."""
import io
import os
import tempfile
import unittest
import zipfile
import hashlib
from pathlib import Path
from unittest.mock import patch

from scripts.build_private_customer_candidate import create_private_candidate,main

class CandidateTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix='codechecker-candidate-synthetic-')
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.exe=self.root/'CodeCheckerOffline.exe'
        self.exe.write_bytes(b'MZ\x00 INERT NEVER RUN ' + b'X'*100)
        self.readme=self.root/'README-owner.txt';self.readme.write_text('사용법\n예제 텍스트만.\n',encoding='utf-8')
        self.license=self.root/'legal-original.txt';self.license.write_text('SYNTHETIC ONLY. not a license.',encoding='utf-8')
        self.notice=self.root/'notice-original.txt';self.notice.write_text('SYNTHETIC NOTICE PLACEHOLDER',encoding='utf-8')
        self.third=self.root/'third.txt';self.third.write_text('SYNTHETIC THIRD SOURCE PLACEHOLDER',encoding='utf-8')
        self.out=self.root/'private-candidate.zip'

    def opts(self):
        return dict(exe=self.exe,readme=self.readme,license_file=self.license,notice=self.notice,
                    component_licenses={'thirdparty.txt':self.third},output=self.out)

    def test_valid_own_inputs_produce_private_zip_structurally_pinned(self):
        before={x:x.read_bytes() for x in (self.exe,self.readme,self.license,self.notice,self.third)}
        p=create_private_candidate(**self.opts())
        self.assertEqual(p['status'],'PRIVATE_CANDIDATE_CREATED_RELEASE_BLOCKED')
        self.assertEqual(p['entries_checked'],6)
        self.assertFalse(p['customer_release_ready'])
        for key in ('original_license_texts_verified','vendor_redistribution_rights_verified','human_windows_acceptance_verified','owner_release_approval'):
            self.assertFalse(p[key])
        self.assertEqual({x:x.read_bytes() for x in before},before)
        with zipfile.ZipFile(self.out) as z:
            self.assertEqual(z.read('CodeCheckerOffline.exe'),before[self.exe])
            self.assertEqual(z.read('LICENSE'),before[self.license])
            self.assertEqual(z.namelist(),sorted(z.namelist()[:-1])+['SHA256SUMS.txt'])
            self.assertEqual(len(z.namelist()),6)
        self.assertNotIn(str(self.root),str(p))

    def test_do_not_overwrite_existing_destination(self):
        self.out.write_bytes(b'PREEXISTING')
        with self.assertRaises(ValueError):create_private_candidate(**self.opts())
        self.assertEqual(self.out.read_bytes(),b'PREEXISTING')

    def test_missing_original_component_document_blocks(self):
        o=self.opts();o['component_licenses']={}
        with self.assertRaises(ValueError):create_private_candidate(**o)
        self.assertFalse(self.out.exists())

    def test_duplicate_logical_component_names_are_casefold_rejected(self):
        another=self.root/'another.txt';another.write_bytes(b'SECOND')
        o=self.opts();o['component_licenses']={'first.txt':self.third,'FIRST.TXT':another}
        with self.assertRaises(ValueError):create_private_candidate(**o)

    def test_traversal_and_malformed_archive_names_rejected(self):
        for name in ('../other.txt','folder/name.txt','bad\\name.txt','', 'hello.exe', 'third party.txt', 'x'*85+'.txt'):
            with self.subTest(name=name):
                o=self.opts();o['component_licenses']={name:self.third}
                with self.assertRaises(ValueError):create_private_candidate(**o)
                self.assertFalse(self.out.exists())

    def test_source_symlink_and_multiple_hardlinks_are_rejected(self):
        link=self.root/'notice-link.txt'
        try:link.symlink_to(self.notice)
        except OSError:self.skipTest('symlink not supported')
        o=self.opts();o['notice']=link
        with self.assertRaises(ValueError):create_private_candidate(**o)
        hard=self.root/'hard.txt';os.link(self.license,hard)
        with self.assertRaises(ValueError):create_private_candidate(**self.opts())

    def test_output_parent_symlink_and_relative_output_are_rejected(self):
        o=self.opts();o['output']=Path('relative.zip')
        with self.assertRaises(ValueError):create_private_candidate(**o)
        link=self.root/'linkedfolder'
        try:link.symlink_to(self.root)
        except OSError:self.skipTest('symlink not supported')
        o['output']=link/'else.zip'
        with self.assertRaises(ValueError):create_private_candidate(**o)

    def test_invalid_notice_utf8_and_binary_controls_fail(self):
        for content in (b'\xff\xfe\xfc',b'a\x00b'):
            self.notice.write_bytes(content)
            with self.assertRaises(ValueError):create_private_candidate(**self.opts())
            self.assertFalse(self.out.exists())

    def test_same_file_used_in_multiple_roles_rejected(self):
        o=self.opts();o['notice']=self.license
        with self.assertRaises(ValueError):create_private_candidate(**o)

    def test_failed_final_validator_rolls_back_only_new_zip(self):
        with patch('scripts.build_private_customer_candidate.inspect_candidate',side_effect=ValueError('simulated verifier fail')):
            with self.assertRaises(ValueError):create_private_candidate(**self.opts())
        self.assertFalse(self.out.exists())
        self.assertTrue(self.exe.exists())

    def test_nonmatching_receipt_fails_without_approval(self):
        with patch('scripts.build_private_customer_candidate.inspect_candidate',return_value={'customer_release_ready':True}):
            with self.assertRaises(ValueError):create_private_candidate(**self.opts())
        self.assertFalse(self.out.exists())

    def test_cli_failure_does_not_print_private_paths(self):
        args=['--exe',str(self.exe),'--readme',str(self.readme),'--license',str(self.license),
              '--notice',str(self.notice),'--component-license','invalid=bad', '--out',str(self.out)]
        with patch('sys.stdout',new_callable=io.StringIO) as s:
            result=main(args)
            self.assertEqual(result,1)
            self.assertNotIn(str(self.root),s.getvalue())
            self.assertIn('PRIVATE_CANDIDATE_BLOCKED',s.getvalue())

if __name__=='__main__':unittest.main()
