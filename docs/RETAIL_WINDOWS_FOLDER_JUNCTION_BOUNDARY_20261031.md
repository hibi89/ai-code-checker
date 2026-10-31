# Code Checker — Windows 정션/재분석 연결 경로 차단

기본 오프라인 Windows 제품은 사용자가 선택한 로컬 폴더의 소스만 읽어야 한다. 일반 심볼릭 링크 제외에 사용하는 `os.walk(followlinks=False)`만으로는 Windows NTFS junction/reparse 디렉터리를 완전히 차단했다고 보장할 수 없다.

## 설계 비교 및 채택

- A: 기존 `is_symlink()` 및 `followlinks=False` 유지. 코드 비용 0이지만 Windows junction이 독립 경로로 탐색될 가능성과 외부 폴더 데이터 누출이 남는다.
- **B: 안전한 하위 폴더 목록을 구성하기 전에 `Path.lstat().st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT`를 검사**(선택). 입력 로더와 읽기 전용 미리보기 pruned-subtree 목록의 판단을 일치시킨다. 또한 `os.walk`의 열거 실패를 더 이상 조용히 무시하지 않는다. 별도 API·패키지·사용자 권한·비용 0.

정상 일반 폴더/파일·ZIP·TXT·붙여넣기·Gemini v1 기능은 보존한다. 재분석 폴더는 읽지 않고 하위 생략 목록에 표시하며, 읽기 실패가 발생하면 `complete` 오판 대신 검사 중단한다. 특별 파일/폴더를 강제로 처리하지 않는다.

테스트는 외부 원본을 사용하지 않는 **임시 합성 폴더, 안전한 심볼릭 링크, `os.walk` 열거 실패 시뮬레이션, 그리고 Windows runner의 실제 `mklink /J` 정션**으로 검증한다. 정션 테스트가 OS 권한으로 SKIP되면 Windows 정션 동작은 **미검증**으로 취급한다.

## 한계

경합 중 디렉터리 링크가 변하는 OS 수준 TOCTOU는 완전 원자적으로 차단했다고 주장하지 않는다. 다른 미확인 reparse/cloud provider, 고객 OS 실제 사용, SmartScreen/Defender/OS 패킷·한국어 PDF, Tcl/Tk 및 71개 구성요소 라이선스·NOTICE, 고객 ZIP 승인 모두 별도 판매 차단 조건이다. 기존 파일 내용을 변경하거나 고객 소스/EXE/라이선스 전문을 GitHub에 올리지 않는다.
