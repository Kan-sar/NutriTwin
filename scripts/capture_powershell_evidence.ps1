param(
    [ValidateSet('capture', 'api', 'tests', 'database')]
    [string]$Mode = 'capture',
    [string]$ReadyFile = ''
)

$ErrorActionPreference = 'Stop'
$Repository = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Evidence = Join-Path $Repository 'docs\review1\evidence'

function Set-EvidenceConsole([string]$Title, [int]$Width, [int]$Height) {
    $Host.UI.RawUI.WindowTitle = $Title
    $Host.UI.RawUI.ForegroundColor = 'Gray'
    $Host.UI.RawUI.BackgroundColor = 'Black'
    $buffer = $Host.UI.RawUI.BufferSize
    $buffer.Width = $Width
    $buffer.Height = 500
    $Host.UI.RawUI.BufferSize = $buffer
    $window = $Host.UI.RawUI.WindowSize
    $window.Width = $Width
    $window.Height = $Height
    $Host.UI.RawUI.WindowSize = $window
    Set-Location $Repository
    Clear-Host
}

function Complete-Evidence([string]$Path) {
    Write-Host ''
    Write-Host 'Capture ready.' -ForegroundColor Green
    New-Item -ItemType File -Path $Path -Force | Out-Null
    Read-Host 'Press Enter to close'
}

if ($Mode -eq 'api') {
    Set-EvidenceConsole 'NutriTwin PowerShell - API workflow' 132 38
    Write-Host 'NutriTwin - live PowerShell API verification' -ForegroundColor Cyan
    Write-Host 'PS C:\Projects\NutriTwin> irm http://127.0.0.1:8000/health/ready | ConvertTo-Json -Depth 5' -ForegroundColor White
    irm 'http://127.0.0.1:8000/health/ready' | ConvertTo-Json -Depth 5
    Write-Host ''
    Write-Host 'PS C:\Projects\NutriTwin> .\.venv\Scripts\python.exe scripts\demo.py' -ForegroundColor White
    & '.\.venv\Scripts\python.exe' 'scripts\demo.py'
    Complete-Evidence $ReadyFile
    exit
}

if ($Mode -eq 'tests') {
    Set-EvidenceConsole 'NutriTwin PowerShell - tests' 150 22
    $outputFile = Join-Path $env:TEMP 'nutritwin-review-tests-output.txt'
    & '.\.venv\Scripts\python.exe' -m pytest --cov --cov-report=term 2>&1 |
        Tee-Object -FilePath $outputFile | Out-Host
    Clear-Host
    Write-Host 'NutriTwin - automated test and coverage verification' -ForegroundColor Cyan
    Write-Host 'PS C:\Projects\NutriTwin> .\.venv\Scripts\python.exe -m pytest --cov --cov-report=term' -ForegroundColor White
    Get-Content -LiteralPath $outputFile | Select-Object -Last 12
    Complete-Evidence $ReadyFile
    exit
}

if ($Mode -eq 'database') {
    Set-EvidenceConsole 'NutriTwin PowerShell - PostgreSQL' 136 42
    $env:COMPOSE_FILE = 'infra/docker/compose.yaml'
    Write-Host 'NutriTwin - live PostgreSQL state through Docker Compose' -ForegroundColor Cyan
    Write-Host "PS C:\Projects\NutriTwin> `$env:COMPOSE_FILE = 'infra/docker/compose.yaml'" -ForegroundColor White
    $aggregateQuery = "SELECT 'data_sources' AS entity, count(*) AS rows FROM data_sources UNION ALL SELECT 'target_snapshots', count(*) FROM target_snapshots UNION ALL SELECT 'meals', count(*) FROM meals UNION ALL SELECT 'audit_events', count(*) FROM audit_events UNION ALL SELECT 'chemical_substances', count(*) FROM chemical_substances UNION ALL SELECT 'food_ontology_mappings', count(*) FROM food_ontology_mappings UNION ALL SELECT 'qualitative_evidence', count(*) FROM qualitative_interaction_evidence ORDER BY entity;"
    Write-Host 'PS C:\Projects\NutriTwin> docker compose exec -T postgres psql -U nutritwin -d nutritwin -c $aggregateQuery' -ForegroundColor White
    & docker compose exec -T postgres psql -U nutritwin -d nutritwin -P pager=off -c $aggregateQuery
    $provenanceQuery = 'SELECT preferred_name, chebi_id, source_version, review_status FROM chemical_substances ORDER BY preferred_name;'
    Write-Host 'PS C:\Projects\NutriTwin> docker compose exec -T postgres psql ... -c $provenanceQuery' -ForegroundColor White
    & docker compose exec -T postgres psql -U nutritwin -d nutritwin -P pager=off -c $provenanceQuery
    Complete-Evidence $ReadyFile
    exit
}

Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class NutriTwinWindowCapture {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
}
'@

function Save-NativeWindow([string]$Title, [string]$Path) {
    $process = Get-Process -Name powershell -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq $Title } |
        Select-Object -First 1
    if ($null -eq $process) { throw "PowerShell window not found: $Title" }
    $rect = New-Object NutriTwinWindowCapture+RECT
    if (-not [NutriTwinWindowCapture]::GetWindowRect($process.MainWindowHandle, [ref]$rect)) {
        throw "Unable to read the PowerShell window rectangle"
    }
    $bitmap = New-Object System.Drawing.Bitmap(($rect.Right - $rect.Left), ($rect.Bottom - $rect.Top))
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $hdc = $graphics.GetHdc()
    try {
        if (-not [NutriTwinWindowCapture]::PrintWindow($process.MainWindowHandle, $hdc, 2)) {
            throw "PrintWindow failed for $Title"
        }
    }
    finally {
        $graphics.ReleaseHdc($hdc)
        $graphics.Dispose()
    }
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose()
}

$captures = @(
    @{ Mode = 'api'; Title = 'NutriTwin PowerShell - API workflow'; File = '02-health-workflow.png' },
    @{ Mode = 'tests'; Title = 'NutriTwin PowerShell - tests'; File = '06-automated-tests.png' },
    @{ Mode = 'database'; Title = 'NutriTwin PowerShell - PostgreSQL'; File = '07-database-state.png' }
)
foreach ($capture in $captures) {
    $ready = Join-Path $env:TEMP ("nutritwin-review-{0}-{1}.ready" -f $capture.Mode, $PID)
    if (Test-Path -LiteralPath $ready) { Remove-Item -LiteralPath $ready -Force }
    $arguments = "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Mode $($capture.Mode) -ReadyFile `"$ready`""
    $process = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WindowStyle Normal -PassThru
    $deadline = (Get-Date).AddMinutes(3)
    while (-not (Test-Path -LiteralPath $ready)) {
        if ((Get-Date) -gt $deadline) { throw "Timed out waiting for $($capture.Mode) evidence" }
        Start-Sleep -Milliseconds 250
    }
    Save-NativeWindow $capture.Title (Join-Path $Evidence $capture.File)
    Stop-Process -Id $process.Id -Force
    Remove-Item -LiteralPath $ready -Force
}
Write-Host "Captured native PowerShell evidence in $Evidence"
