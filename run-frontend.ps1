$env:APP_ENV = "development"
if (-not $env:BACKEND_URL) { $env:BACKEND_URL = "http://127.0.0.1:8009" }
if (-not $env:FRONTEND_URL) { $env:FRONTEND_URL = "http://127.0.0.1:3009" }
Set-Location "$PSScriptRoot\frontend"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 3009
