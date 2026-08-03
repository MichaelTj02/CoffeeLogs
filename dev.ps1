#Requires -Version 5.1
<#
Starts both dev servers, each in its own window:
  backend  http://localhost:8000  (docs at /docs)
  frontend http://localhost:3000
Stop either with Ctrl+C in its window.
#>

$root = $PSScriptRoot

$mysql = Get-Service MySQL80 -ErrorAction SilentlyContinue
if ($null -eq $mysql) {
    Write-Warning "Service MySQL80 not found. The backend has no SQLite fallback and will fail on every query."
}
elseif ($mysql.Status -ne "Running") {
    Write-Warning "MySQL80 is $($mysql.Status). Start it first: Start-Service MySQL80  (needs an elevated shell)"
}

# Calling the venv's uvicorn.exe directly is what Activate.ps1 would have set up anyway --
# activation only prepends .venv\Scripts to PATH for the session.
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\backend'; .\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host "backend  -> http://localhost:8000/docs"
Write-Host "frontend -> http://localhost:3000"
