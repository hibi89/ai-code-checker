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
            ("cancel", "cancelled"),
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

            def until(predicate, label: str, then, started=None) -> None:
                started = time.monotonic() if started is None else started
                if time.monotonic() - started > 12 or time.monotonic() > deadline:
                    snapshot = (
                        " busy=" + str(window.busy)
                        + " preview=" + str(window.preview_request is not None)
                        + " scan_button=" + str(window.scan_button["state"])
                        + " ttk_disabled=" + str(window.scan_button.instate(["disabled"]))
                        + " state=" + window.state_var.get()
                        + " queue=" + str(window.queue.qsize())
                    )
                    fail("TIMEOUT " + label + snapshot)
                    return
                try:
                    if predicate():
                        then()
                    else:
                        window.root.after(30, lambda: until(predicate, label, then, started))
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
                    # Reopen a previous report by explicit picker without restoring
                    # in-session delete authority. Reject an unrelated HTML file.
                    window.last_result = None
                    window.delete_button.configure(state="disabled")
                    window.output_var.set(str(report_root))
                    with patch(
                        "tkinter.filedialog.askopenfilename", return_value=str(saved_reports[0])
                    ), patch("os.startfile") as open_history:
                        window.history_button.invoke()
                        open_history.assert_called_once_with(str(saved_reports[0].absolute()))
                    if window.last_result is not None or not window.delete_button.instate(["disabled"]):
                        fail("historical report gained deletion authority")
                        return
                    unrelated = report_root / "unrelated.html"
                    unrelated.write_text("<html>untrusted</html>", encoding="utf-8")
                    with patch(
                        "tkinter.filedialog.askopenfilename", return_value=str(unrelated)
                    ), patch("os.startfile") as blocked_open, patch(
                        "tkinter.messagebox.showerror"
                    ) as denied:
                        window.history_button.invoke()
                        blocked_open.assert_not_called()
                        denied.assert_called_once()
                    if window.last_result is not None:
                        fail("untrusted historical HTML changed active report state")
                        return
                    results.append("historical report read-only open and denial PASS")
                    # Use the actual Tk recent-list dialog and choose an entry;
                    # this is not an interactive consumer Windows acceptance test.
                    from tkinter import Listbox, Toplevel

                    def descendants(widget):
                        yield widget
                        for child in widget.winfo_children():
                            yield from descendants(child)

                    with patch("os.startfile") as opened_recent, patch(
                        "tkinter.messagebox.showinfo", side_effect=AssertionError("recent list unexpectedly empty")
                    ), patch(
                        "tkinter.messagebox.showerror", side_effect=AssertionError("recent list unexpectedly rejected")
                    ):
                        window.recent_button.invoke()
                        dialogs = [
                            child for child in window.root.winfo_children()
                            if isinstance(child, Toplevel)
                        ]
                        if len(dialogs) != 1:
                            fail("recent report chooser did not create exactly one dialog")
                            return
                        chooser = dialogs[0]
                        entries = [child for child in descendants(chooser) if isinstance(child, Listbox)]
                        if len(entries) != 1:
                            fail("recent chooser missing listbox")
                            return
                        listbox = entries[0]
                        if set(listbox.get(0, "end")) != {path.name for path in saved_reports}:
                            fail("recent chooser offered invalid or missing reports")
                            return
                        choose_buttons = [
                            child for child in descendants(chooser)
                            if child.winfo_class() == "TButton"
                            and child.cget("text") == "선택한 보고서 열기"
                        ]
                        if len(choose_buttons) != 1:
                            fail("recent chooser missing open command")
                            return
                        chosen_filename = listbox.get(0)
                        choose_buttons[0].invoke()
                        opened_recent.assert_called_once_with(str((report_root / chosen_filename).absolute()))
                        if chooser.winfo_exists():
                            fail("recent chooser remained open after selection")
                            return
                    if window.last_result is not None or not window.delete_button.instate(["disabled"]):
                        fail("recent history chooser granted deletion permission")
                        return
                    results.append("Tk recent-report chooser read-only open PASS")
                    # Validate folder-to-child-output denial on the Windows runner,
                    # before source ingestion and before any output directory is made.
                    from code_input import InputError
                    from desktop_core import ScanRequest, run_scan
                    forbidden_output = folder / "inside-project" / "reports"
                    try:
                        run_scan(
                            ScanRequest("path", source=str(folder)),
                            forbidden_output, "must-not-write",
                        )
                    except InputError:
                        if forbidden_output.exists():
                            fail("denied output nevertheless created files")
                            return
                        results.append("Windows project-output containment blocked PASS")
                    else:
                        fail("scan wrote reports under the scanned project")
                        return
                    # Exercise the real Tk delete button against a separately
                    # generated synthetic report, preserving the four prior reports.
                    from desktop_core import ScanRequest, run_scan
                    try:
                        cleanup_result = run_scan(
                            ScanRequest("paste", text="eval('1')\n", language="python"),
                            report_root, "code-checker-gui-cleanup-e2e",
                        )
                        # A report changed on disk must never be launched
                        # through the trusted current-report button. Keep this
                        # synthetic fixture separate from historical reports.
                        tamper_result = run_scan(
                            ScanRequest("paste", text="eval('synthetic')\n", language="python"),
                            rootdir / "tampered-open-fixture", "current-tamper",
                        )
                        window.last_result = tamper_result
                        window.open_button.configure(state="normal")
                        old_html = tamper_result.html_path.read_bytes()
                        changed_html = old_html.replace(b"<title>", b"<TITLE>", 1)
                        if changed_html == old_html:
                            fail("missing report title fixture to tamper")
                            return
                        tamper_result.html_path.write_bytes(changed_html)
                        with patch("os.startfile") as denied_open, patch(
                            "tkinter.messagebox.showerror"
                        ) as warned:
                            window.open_button.invoke()
                            denied_open.assert_not_called()
                            warned.assert_called_once()
                        results.append("Tk current report tamper-open blocked PASS")
                        window.last_result = cleanup_result
                        window.delete_button.configure(state="normal")
                        with patch("tkinter.messagebox.askyesno", return_value=False):
                            window.delete_button.invoke()
                        if not cleanup_result.html_path.exists() or not cleanup_result.markdown_path.exists():
                            fail("declined deletion removed files")
                            return
                        with patch("tkinter.messagebox.askyesno", return_value=True):
                            window.delete_button.invoke()
                        if cleanup_result.html_path.exists() or cleanup_result.markdown_path.exists():
                            fail("approved deletion left report pair")
                            return
                        if window.last_result is not None or not window.open_button.instate(["disabled"]):
                            fail("deleted report remains active")
                            return
                        if not window.delete_button.instate(["disabled"]):
                            fail("deleted report button still enabled")
                            return
                        if not all(p.exists() for p in saved_reports):
                            fail("deleting current report removed old reports")
                            return
                        results.append("confirmed current-session report pair delete PASS")
                    except Exception as exc:
                        fail("report cleanup Tk error: " + repr(exc))
                        return
                    window.root.destroy()
                    return
                name, expected = scenarios[scenario_index]
                old_result = window.last_result
                try:
                    if name in {"txt", "zip", "blocked", "cancel"}:
                        selected = {
                            "txt": txt, "zip": zip_path,
                            "blocked": invalid_zip, "cancel": txt,
                        }[name]
                        with patch("tkinter.filedialog.askopenfilename", return_value=str(selected)):
                            window.file_button.invoke()
                        if name in {"txt", "cancel"}:
                            window.language_var.set("Python")
                    elif name == "folder":
                        with patch("tkinter.filedialog.askdirectory", return_value=str(folder)):
                            window.folder_button.invoke()
                    else:
                        window.paste_button.invoke()
                        window.paste_text.delete("1.0", "end")
                        window.paste_text.insert("1.0", "print('paste')\n")
                        window.language_var.set("Python")
                        window.paste_filename_var.set("client-sample.py")
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
                    if name == "paste":
                        if (window.preview_request.filename != "client-sample.py"
                                or "client-sample.py" not in window.result_text.get("1.0", "end")):
                            fail("paste virtual filename not visible in Tk preview")
                            return
                    if expected == "blocked":
                        if window.preview_request is not None:
                            fail("blocked input was preview-approved")
                            return
                        if not window.open_button.instate(["disabled"]) or window.last_result is not None:
                            fail("blocked input left stale prior HTML result openable")
                            return
                        results.append("blocked input rejected; stale report not reopenable")
                        advance()
                        return
                    if window.scan_button.instate(["disabled"]):
                        fail(
                            name + ": scan button truly disabled after preview:"
                            + " cget=" + str(window.scan_button["state"])
                            + " preview=" + str(window.preview_request is not None)
                            + " busy=" + str(window.busy)
                            + " state=" + window.state_var.get()
                        )
                        return
                    if name == "cancel":
                        from desktop_core import ScanCancelled
                        from unittest.mock import patch as local_patch

                        # Isolate UI cancellation from machine speed: a synthetic
                        # worker pauses until the Tk button sends the cancel event.
                        def cancellable_worker(
                            _req, _folder, _name, *,
                            control=None, expected_preview_fingerprint=None,
                        ):
                            if control is None:
                                raise AssertionError("missing GUI cancellation control")
                            if not expected_preview_fingerprint or len(expected_preview_fingerprint) != 64:
                                raise AssertionError("GUI omitted the preview freshness token")
                            control.emit("scan", 0, 2)
                            if not control.cancel_requested.wait(4):
                                raise AssertionError("Tk cancellation was not sent")
                            control.check()
                            raise AssertionError("cancelled task continued")

                        patcher = local_patch("desktop_ui.run_scan", side_effect=cancellable_worker)
                        patcher.start()
                        window.scan_button.invoke()
                        if window.cancel_button.instate(["disabled"]):
                            patcher.stop()
                            fail("cancel button disabled during active scan")
                            return
                        window.cancel_button.invoke()

                        def after_cancel() -> None:
                            patcher.stop()
                            if window.last_result is not None:
                                fail("cancelled job exposed stale report")
                                return
                            if "작업 취소됨" not in window.state_var.get():
                                fail("cancelled job not labelled cancelled")
                                return
                            if not window.open_button.instate(["disabled"]):
                                fail("cancelled job left HTML open enabled")
                                return
                            if (report_root / "cancelled.html").exists():
                                fail("cancelled job produced report")
                                return
                            results.append("cancel button and Tk worker cancellation PASS")
                            advance()
                        until(lambda: not window.busy, "cancel worker", after_cancel)
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
                        if window.open_button.instate(["disabled"]):
                            fail(name + ": open HTML button truly disabled")
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
        if errors or rc != 0 or len(results) != 11:
            print("GUI_E2E_FAILURE: " + json.dumps(errors, ensure_ascii=False), file=sys.stderr)
            return 1
        print("WINDOWS_TK_WIDGET_INTEGRATION_PASS")
        print("SYNTHETIC_GUI_SOCKET_CONNECT_ATTEMPTS=0")
        print("PHYSICAL_CLICK_AND_CLEAN_USER_PC=UNVERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
