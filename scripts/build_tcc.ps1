[CmdletBinding()]
param(
    [string]$OutputDir,
    [switch]$AllowBancaPlaceholders
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutputDir = if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    Join-Path $root "output\pdf"
}
else {
    [System.IO.Path]::GetFullPath($OutputDir)
}
$source = Join-Path $root "latex_tcc\main.tex"
$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
$xelatexPath = if ($xelatex) {
    $xelatex.Source
}
else {
    Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64\xelatex.exe"
}

if (-not (Test-Path $xelatexPath)) {
    throw "XeLaTeX não foi encontrado. Instale MiKTeX ou TeX Live e execute novamente."
}

$sourceText = Get-Content -Raw -Encoding utf8 $source
$blockedTerms = @("RESULTADOS ESPERADOS", "\\chapter{CRONOGRAMA}", "Relatório de Conformidade")
foreach ($term in $blockedTerms) {
    if ($sourceText.Contains($term)) {
        throw "O fonte canônico contém o termo obsoleto: $term"
    }
}
if (-not $AllowBancaPlaceholders -and $sourceText.Contains("Prof. Xxxxxxxxxxxxxxxxxxxxxxx")) {
    throw "Preencha a banca ou use -AllowBancaPlaceholders apenas para gerar uma prova de revisão."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Push-Location (Split-Path $source)
try {
    1..2 | ForEach-Object {
        & $xelatexPath "-interaction=nonstopmode" "-halt-on-error" "-output-directory=$OutputDir" "main.tex"
        if ($LASTEXITCODE -ne 0) {
            throw "XeLaTeX falhou na passagem $_. Consulte o log em $OutputDir."
        }
    }
}
finally {
    Pop-Location
}

$generated = Join-Path $OutputDir "main.pdf"
if (-not (Test-Path $generated)) {
    throw "A compilação terminou sem gerar main.pdf."
}

$finalName = if ($AllowBancaPlaceholders) {
    "TCC_Privacy_by_Design_2026_PROVA_COM_PLACEHOLDERS.pdf"
}
else {
    "TCC_Privacy_by_Design_2026.pdf"
}
$final = Join-Path $OutputDir $finalName
Copy-Item -LiteralPath $generated -Destination $final -Force
if ($AllowBancaPlaceholders) {
    Write-Host "PDF de prova gerado em: $final"
}
else {
    Write-Host "PDF canônico gerado em: $final"
}
Write-Host "Próximo passo obrigatório: renderizar o PDF em PNG e revisar todas as páginas."
