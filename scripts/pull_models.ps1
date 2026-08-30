# Pull the models configured in .env / registry for the Sovereign AI Workbench.
# The system does NOT auto-download models; run this explicitly when you are
# ready to download models onto your machine.
param(
    [switch]$SkipEmbedding
)

$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim())
        }
    }
}

$models = @(
    $env:OLLAMA_GENERAL_MODEL,
    $env:OLLAMA_REASONING_MODEL,
    $env:OLLAMA_CODING_MODEL,
    $env:OLLAMA_VISION_MODEL
)
if (-not $SkipEmbedding) {
    $models += if ($env:OLLAMA_EMBEDDING_MODEL) { $env:OLLAMA_EMBEDDING_MODEL } else { 'nomic-embed-text' }
}

$ollamaBase = if ($env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL } else { 'http://localhost:11434' }
Write-Host "Pulling models via $ollamaBase ..."

foreach ($m in $models) {
    if ([string]::IsNullOrWhiteSpace($m)) { continue }
    Write-Host "==> ollama pull $m"
    & ollama pull $m
}

Write-Host "Done. Verify with: ollama list"
