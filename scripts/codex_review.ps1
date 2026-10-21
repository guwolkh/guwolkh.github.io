# Codex에게 홈페이지 검수를 맡기고 결과를 검수\결과\ 에 저장한다 (결과 폴더는 공개 저장소에 올리지 않음).
# 사용:
#   특정 페이지: powershell -ExecutionPolicy Bypass -File scripts\codex_review.ps1 dizziness/recurrent-bppv
#   최근 변경분: powershell -ExecutionPolicy Bypass -File scripts\codex_review.ps1 changes
# 필요: Codex CLI(또는 Codex 앱) + ChatGPT 로그인. 옵션이 다르면 `codex exec --help`로 확인하고 고친다.
param([Parameter(Mandatory = $true)][string]$Target)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$root = Split-Path -Parent $PSScriptRoot
$bg = "D:\guwol-youtube\배경자료"
if (-not (Test-Path $bg)) { Write-Warning "배경자료 폴더가 없습니다: $bg (경로가 다르면 이 파일의 `$bg를 고치세요)" }

if ($Target -eq "changes") {
    $what = "최근 변경분(git diff HEAD~1 과 아직 커밋하지 않은 변경)"
    $name = "변경분"
} else {
    $slug = $Target.Trim().Trim('/')
    if (-not (Test-Path (Join-Path $root "src\pages\$($slug -replace '/', '\').html"))) { throw "페이지가 없습니다: src\pages\$slug.html" }
    $what = "src/pages/$slug.html 과 site.config.json 의 slug '$slug' 항목"
    $name = $slug -replace '/', '_'
}

$prompt = "AGENTS.md 절차대로 $what 을 검수해. 기준 파일은 $bg 의 01·02·03, site.config.json, 검수 폴더의 칼럼_작성방식.md·본능_반박_리스트.md. 결과는 검수/체크리스트_홈페이지.md 형식의 마크다운으로만 출력해. 어떤 파일도 고치지 마."

$outDir = Join-Path $root "검수\결과"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir ("{0}_{1}.md" -f (Get-Date -Format "yyyy-MM-dd_HHmm"), $name)

$codex = (Get-Command codex -ErrorAction SilentlyContinue).Source
if (-not $codex) {
    $codex = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin" -Recurse -Filter codex.exe -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $codex) { throw "codex 명령을 찾을 수 없습니다. Codex를 설치하고 로그인하세요." }

Push-Location $root
try {
    & $codex exec --sandbox read-only --color never -C $root -o $out $prompt
    if ($LASTEXITCODE -ne 0) { throw "codex exec 실패 (종료 코드 $LASTEXITCODE)" }
} finally { Pop-Location }
Write-Host "검수 결과 저장: $out"
