# Starts Passly in THIS terminal: API on port 8010 + website on port 8502.
# Usage:  .\run.ps1        (press Ctrl+C to stop both)
$root = $PSScriptRoot
$py = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$env:BACKEND_URL = "http://127.0.0.1:8010"

# API runs in the background of this same terminal (no extra window).
$api = Start-Process -FilePath $py -ArgumentList "-m", "uvicorn", "main:app", "--port", "8010" `
    -WorkingDirectory (Join-Path $root "backend") -NoNewWindow -PassThru

try {
    Set-Location $root
    Write-Host "`n  Passly is starting... open http://localhost:8502`n" -ForegroundColor Cyan
    & $py -m streamlit run frontend/app.py --server.port 8502
}
finally {
    # Ctrl+C stops the website; make sure the API stops too.
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}
