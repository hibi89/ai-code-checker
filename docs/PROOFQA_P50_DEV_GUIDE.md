# PROOFQA AX — P50 개발자 전용 오프라인 검수 CLI

**상태:** P50 기능 후보. 정확 SHA 테스트/독립 검수 후 P50 내부 게이트 판정. 고객 판매·보안 인증·외부 접근 **불가(RELEASE HOLD)**.

## 실행

Python 3.11+ 및 기존 ai-code-checker 저장소의 소스만 사용합니다. 설치·외부 API·Gemini·Graphify·브라우저 호출 없이 ZIP을 읽기 전용으로 분석합니다.

```bash
python -m unittest tests.test_proofqa_p50 -v
python proofqa_p50.py ./synthetic-project.zip --output-dir ./proofqa-reports
```

- 입력: **로컬 단일 ZIP 파일** (최대 ZIP 20MiB, 압축 해제 합계 8MiB, 엔트리 1,000개, 파일당 1MiB). 폴더·Git 원격·staging URL은 아직 P50 CLI에서 미지원입니다.
- 기존 `offline_core.scan_path`/ `offline_report.build_report` / `render_html`을 **그대로 호출**하여 언어 제한과 Python 정적 분석 근거를 승계하며 Code Checker 원본 모듈은 수정하지 않습니다.
- ZIP을 디스크에 압축 해제하거나 고객 코드/스크립트/postinstall을 실행하지 않습니다. ZIP slip, 중복 이름(대소문자·Unicode NFC), 링크/장치, 암호화, 압축비·크기 초과를 차단합니다.
- 분석 전후 ZIP 원본 SHA256을 비교해 원본 변경 시 납품을 차단합니다. **원본 변경 후 재복구는 자동 수행하지 않습니다.**
- 출력: 새 `proofqa-<digest16>` 폴더의 `case.json`, `report.html`, `manifest.json`. 기존 이름은 덮어쓰지 않습니다. JSON 소스 원문·비밀값을 포함하지 않으며, 로컬 HTML은 기존 Code Checker 마스킹 규칙을 따르지만 고객 경로·발췌 등 민감한 정보가 남을 수 있으니 외부 공유하지 마세요.
- 독립 재확인: `python -c "from proofqa_p50 import verify_delivery; verify_delivery('proofqa-reports/proofqa-...')"`. Manifest가 원본 ZIP 해시와 보고서 바이트를 묶지만, 이는 취약점 검증이나 고객 인수가 아닙니다.
- Exit: `0` 기존 정적 분석 범위 완료, `3` 부분 분석, `2` 차단. `0`이라도 안전하거나 취약점이 없다는 뜻이 아닙니다.

## 설계 비교
A안(원본 CLI 직접 확장): 실행 경로/영향도 작아 보이나 기존 Code Checker 고객 제품과 목적·버전·회귀가 섞임. B안(새 `proofqa_p50.py` 얇은 adapter, **채택**): 기존 정적 엔진 소스 보존·작업량 작음·P70 Graph/Browser 분리 가능. C안(외부 AI/Graph/Browser를 P50에 일괄 추가): 비용·라이선스·권한·보안 범위가 커지고 실제 증빙 부족으로 기각.

## P50 현재 미검증/제외
Graphify pinned CLI, agent-browser, Cloudflare 독립 감사, 고객 staging·실기기 Windows, OS 수준 파일·네트워크 격리, 고객 원본·권리/서면 인수, PDF/ZIP 최종 납품, 라이선스/서명/스마트스크린은 **미수행**입니다. P50 CLI는 안전하지 않은 고객 프로그램을 실행하지 않지만, OS 커널 수준의 샌드박스 제공을 의미하지 않습니다.

## 추적
- 설계 정본: `hibi89/Freelancer@product/proofqa-ax-delivery-audit/docs/FINAL_BLUEPRINT.md`
- P50 정확 수용: `docs/ACCEPTANCE_AND_ROADMAP.md`
- 소스: `proofqa_p50.py`; 합성 테스트: `tests/test_proofqa_p50.py`
- 30개 위협 모델 전체, 2개 고객 검수는 P95 이후. **중앙 공식 최종설계 완성률은 별도 승인·검증 전 UNASSESSED**.
