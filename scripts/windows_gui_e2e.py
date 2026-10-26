"""Synthetic Windows Tk widget integration: launch real root and invoke UI controls.

No real customer sources, screenshot upload, API call or browser/network access.
This covers scripted Tk widget callbacks on Windows runner, NOT a person
clicking a clean customer machine and NOT Defender/SmartScreen.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

from desktop_ui import launch


def main() -> int:
    if sys.platform != "win32":
        print("Windows-only Tk GUI smoke", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="code-checker-gui-") as tmp:
        rootdir = Path(tmp)
        srcdir = rootdir / "한글 경로 테스트"
        srcdir.mkdir()
        txt = srcdir / "검사 대상.txt"
        txt.write_text("print('safe')\neval('1+1')\n", encoding="utf-8")
        before = txt.read_bytes()
        zip_path = rootdir / "mixed.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("core.py", "print('safe')\n")
            archive.writestr("index.js", "const value = 1;\n")
        folder = rootdir / "folder"
        folder.mkdir()
        (folder / "good.py").write_text("print('ok')\n", encoding="utf-8")
        (folder / ".git").mkdir()
        (folder / ".git" / "ignored.py").write_text("print('skipped')\n", encoding="utf-8")
        invalid_zip = rootdir / "invalid.zip"
        with zipfile.ZipFile(invalid_zip, "w") as archive:
            archive.writestr("../escape.py", "print('should-not-read')\n")
        report_root = rootdir / "한국어 출력"
        report_root.mkdir()
        results: list[str] = []
        saved_reports: list[Path] = []
        errors: list[str] = []
        scenario_index = 0
        scenarios = [
            ("txt", "complete"),
            ("zip", "partial"),
            ("folder", "partial"),
            ("paste", "complete"),
            ("blocked", "blocked"),
        ]
        deadline = time.monotonic() + 75
        dummy_connect = AssertionError("offline Python GUI must not create sockets")

        def on_ready(window):
            nonlocal scenario_index

            def fail(message: str) -> None:
                errors.append(message)
                try:
                    window.root.destroy()
                except Exception:
                    pass

            def until(predicate, label: str, then) -> None:
                if time.monotonic() > deadline:
                    fail("TIMEOUT " + label)
                    return
                try:
                    if predicate():
                        then()
                    else:
                        window.root.after(30, lambda: until(predicate, label, then))
                except Exception as exc:
                    fail(label + " " + type(exc).__name__ + ": " + str(exc))

            def begin() -> None:
                nonlocal scenario_index
                if scenario_index == len(scenarios):
                    if txt.read_bytes() != before:
                        fail("source modified")
                        return
                    if len(saved_reports) != 4:
                        fail("report count incorrect")
                        return
                    if not all(p.exists() and p.with_suffix(".md").exists() for p in saved_reports):
                        fail("paired HTML Markdown missing")
                        return
                    window.root.destroy()
                    return
                name, expected = scenarios[scenario_index]
                old_result = window.last_result
                try:
                    if name in {"txt", "zip", "blocked"}:
                        selected = {"txt": txt, "zip": zip_path, "blocked": invalid_zip}[name]
                        with patch("tkinter.filedialog.askopenfilename", return_value=str(selected)):
                            window.file_button.invoke()
                        if name == "txt":
                            window.language_var.set("Python")
                    elif name == "folder":
                        with patch("tkinter.filedialog.askdirectory", return_value=str(folder)):
                            window.folder_button.invoke()
                    else:
                        window.paste_button.invoke()
                        window.paste_text.delete("1.0", "end")
                        window.paste_text.insert("1.0", "print('paste')\n")
                        window.language_var.set("Python")
                    window.output_var.set(str(report_root))
                    window.root.update_idletasks()
                    window.preview_button.invoke()
                except Exception as exc:
                    fail(name + " SELECT " + repr(exc))
                    return

                def preview_ready() -> bool:
                    if window.busy:
                        return False
                    if expected == "blocked":
                        return "실패/차단" in window.state_var.get()
                    return window.preview_request is not None

                def after_preview() -> None:
                    if expected == "blocked":
                        if window.preview_request is not None:
                            fail("blocked input was preview-approved")
                            return
                        if window.open_button["state"] != "disabled" or window.last_result is not None:
                            fail("blocked input left stale prior HTML result openable")
                            return
                        results.append("blocked input rejected; stale report not reopenable")
                        advance()
                        return
                    if window.scan_button["state"] != "normal":
                        fail(name + ": scan button disabled after preview")
                        return
                    window.scan_button.invoke()

                    def scanned() -> bool:
                        return (
                            not window.busy
                            and window.last_result is not None
                            and window.last_result is not old_result
                        )

                    def after_scan() -> None:
                        result = window.last_result
                        if result.status != expected:
                            fail(name + ": expected " + expected + " got " + result.status)
                            return
                        if result.html_path.parent != report_root:
                            fail("report written outside explicitly selected folder")
                            return
                        if name == "folder" and result.pruned_subtrees != 1:
                            fail("folder excluded subtree not disclosed")
                            return
                        if name == "zip" and result.limited != 1:
                            fail("generic-only JS file not marked limited")
                            return
                        if window.open_button["state"] != "normal":
                            fail(name + ": open HTML button unavailable")
                            return
                        with patch("os.startfile") as open_local:
                            window.open_button.invoke()
                            open_local.assert_called_once_with(str(result.html_path.resolve()))
                        saved_reports.append(result.html_path)
                        results.append(name + " " + result.status + " GUI report/open PASS")
                        advance()

                    until(scanned, name + " scan", after_scan)

                until(preview_ready, name + " preview", after_preview)

            def advance() -> None:
                nonlocal scenario_index
                scenario_index += 1
                window.root.after(25, begin)

            if not window.root.winfo_exists() or not window.file_button.winfo_exists():
                fail("Tk widget creation failed")
                return
            results.append("Tk root and widgets created")
            begin()

        try:
            with patch("socket.socket.connect", side_effect=dummy_connect), patch(
                "socket.create_connection", side_effect=dummy_connect
            ):
                rc = launch(on_ready=on_ready)
        except Exception as exc:
            errors.append("GUI launch " + repr(exc))
            rc = 1
        for result in results:
            print("GUI_E2E: " + result)
        if errors or rc != 0 or len(results) != 6:
            print("GUI_E2E_FAILURE: " + json.dumps(errors, ensure_ascii=False), file=sys.stderr)
            return 1
        print("WINDOWS_TK_WIDGET_INTEGRATION_PASS")
        print("SYNTHETIC_GUI_SOCKET_CONNECT_ATTEMPTS=0")
        print("PHYSICAL_CLICK_AND_CLEAN_USER_PC=UNVERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
