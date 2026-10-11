# 구월경희한의원 홈페이지

기획서: `구월경희한의원_홈페이지_기획서.md`

## 미리보기
```
python serve.py
```
브라우저에서 http://localhost:8080 을 엽니다. 파일을 고친 뒤 새로고침하면 바로 반영됩니다.

## 어디를 고치나요
| 바꿀 것 | 파일 |
|---|---|
| 주소, 전화, 진료시간, 예약·카톡·톡톡·블로그 링크, 진료 분야별 블로그 글, 상담일지 카드 | `site.config.json` |
| 문구(첫 화면, 약력, 진료 과정 등) | `src/index.html` |
| 색, 글자 크기, 배치 | `src/style.css` |
| 원장 사진 | `images/` 폴더 (파일 이름이 바뀌면 `site.config.json`의 `director.photo`도 수정) |

- 값을 비워 두면(`""`) 해당 버튼은 "준비 중"으로 표시됩니다.
- `python build.py`를 실행할 때마다 기획서 5번 표현 기준(완치, 효과 수치, '전문' 수식, 최상급, 결과 문구, 전후 비교)을 자동으로 검사해 경고를 띄웁니다.

## 배포 (GitHub Pages)
- 주소: https://guwolkh.github.io (저장소 github.com/guwolkh/guwolkh.github.io, 공개)
- 고친 내용을 커밋해서 올리면(`git push`) 1~2분 뒤 자동으로 반영됩니다.
- 매년 1월 1일 0시에 자동으로 다시 빌드합니다. 단, GitHub는 60일 넘게 커밋이 없는 저장소의 예약 실행을 멈출 수 있습니다. 이때는 GitHub 저장소 > Actions > "홈페이지 배포" > Run workflow 를 누르면 됩니다.
- 기획서(`*기획서*.md`)는 `.gitignore`로 빼 두어 공개 저장소에 올라가지 않습니다.

### guwolkh.com 구매 후 할 일
1. 도메인 업체 DNS 설정: `A` 레코드 4개(185.199.108.153 / 185.199.109.153 / 185.199.110.153 / 185.199.111.153), `www` 는 `CNAME` → `guwolkh.github.io`
2. GitHub 저장소 > Settings > Pages > Custom domain 에 `guwolkh.com` 입력, 인증서 발급 후 "Enforce HTTPS" 체크
3. `site.config.json`의 `siteUrl`을 `https://guwolkh.com`으로 바꾸고 커밋·푸시
4. 네이버 서치어드바이저·구글 서치콘솔에 `https://guwolkh.com` 등록 후 `sitemap.xml` 제출

도메인을 사기 전에 2번을 하면 사이트가 열리지 않으니 순서를 지켜 주세요.
