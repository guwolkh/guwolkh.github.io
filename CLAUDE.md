# 구월경희한의원 홈페이지 — Claude Code 작업 규칙

- 사실·원장님 관점·표현 규칙의 기준은 `D:\guwol-youtube\배경자료\` (01·02·03). 홈페이지에 쓰는 값은 `site.config.json` 한 곳에서 고친다.
- 칼럼(질문형 페이지)은 `검수/칼럼_작성방식.md`를 따른다. 본능 분석(실력·진정성)과 반박 제거를 적용하고, 반박은 `검수/본능_반박_리스트.md`에서 고른다.
- 수정 순서: 고치기 → `python build.py`(표현 검사) → `D:\guwol-site-audit\run_audit.bat auto`(AI 검색 점검) → Codex 검수 `powershell -ExecutionPolicy Bypass -File scripts\codex_review.ps1 changes` → 결과의 지적마다 "반영 / 반영 안 함 + 이유" 판단 → 의견이 갈리면 원장님 결정 → 원장님 확인 후 커밋·푸시.
- Codex 지적을 그대로 따르지 않는다. 근거(배경자료·원문)로 판단한다. Codex가 제안한 새 규칙은 원장님 승인 뒤에만 반영한다.
- 가격·할인: `/npay/`에 정가만 쓴다. 할인율은 홈페이지에 쓰지 않는다.
- 공개 저장소다. 기획서·검수 결과(`검수/결과/`)는 올리지 않는다.
