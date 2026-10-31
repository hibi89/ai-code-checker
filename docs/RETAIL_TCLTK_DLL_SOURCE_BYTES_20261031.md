# Code Checker — Windows 실제 Tcl/Tk DLL 바이트 출처 검증

본 도구는 실제 Windows PyInstaller EXE의 Tcl/Tk DLL 각각을 디스크로 추출하거나 실행하지 않고 **바이너리 SHA-256**을 계산한다. PyInstaller Analysis-00.toc가 기록한 정확한 빌드 파일(경로 중복 허용 안 함)의 바이트 해시와 비교하고, EXE 감사 SHA와 EXE 내부 실행으로 얻은 Tcl/Tk 런타임 버전 증거까지 동일 파일에 결합한다.

## 방법 비교

A. DLL 파일명/Tcl-Tk 버전 표시만 확인: 빠르지만 실제 포함 바이트 출처는 검증하지 못한다.
B. **실제 EXE의 압축 CArchive DLL ↔ 실제 로컬 빌드 소스 DLL 바이트 2개 대조(채택)**: 기존 PyInstaller API와 표준 라이브러리 사용, 신규 비용·외부 네트워크 0, 소스 경로·DLL 전문 비공개. 잘못된 EXE/빌드·바이트 변화는 거부한다.

기존 Windows 빌드가 생성한 로컬 파일을 대상으로 실행:

```powershell
python -m scripts.verify_frozen_tcltk_dll_provenance --exe dist-windows/CodeCheckerOffline.exe --audit .build-windows/frozen-exe-evidence.json --runtime-receipt .build-windows/runtime-version-receipt.json --analysis-toc .build-windows/CodeCheckerOffline/Analysis-00.toc --out .build-windows/tcltk-exact-dll-provenance.json
```

이 검증은 **빌드 소스 파일이 실제 EXE에 들어간 바이트와 동일하다**는 증거만 제공한다. 그 파일의 법률적 공급자·원 저작권·정확 설치 Tcl license.terms·변형사항·NOTICE 충족, 71개 다른 구성품의 권리, 실제 소비자 Windows·PDF·Defender 수락이나 판매 승인을 증명하지 않는다.

기존 최근 Windows CI에서 Tcl/Tk patchlevel 8.6.15/8.6.15, installed Tcl license.terms 0개, Tk 1개, 별도 미분류 71개로 판정돼 있었다. 공식 upstream 원문 해시 Tcl d8049cd9e7ca055f7e584a76f88861a294b30c9c, Tk 01264352c87ca7e34771bd1ee18bed5201ef139f는 확인됐으나 실제 DLL의 저작권 및 재배포 권한 검토는 여전히 필요하다. 결과 JSON의 모든 판매·권리 승인 플래그는 False 고정이다. EXE/원문 라이선스/개인 증거를 공개 GitHub artifact에 업로드하지 않는다.
