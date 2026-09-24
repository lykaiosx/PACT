param(
 [Parameter(Mandatory=$true)][string]$RuntimeDirectory,
 [Parameter(Mandatory=$true)][string]$InnoCompiler
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force package\runtime,package\app,dist | Out-Null
if ((Resolve-Path $RuntimeDirectory).Path -ne (Resolve-Path package\runtime).Path) {
 Get-ChildItem -LiteralPath $RuntimeDirectory | Copy-Item -Destination package\runtime -Recurse -Force
}
Copy-Item app\* -Destination package\app -Recurse -Force
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:winexe /platform:x64 /win32icon:app\assets\pact.ico /reference:System.Windows.Forms.dll /out:package\PACT.exe Launcher.cs
if ($LASTEXITCODE -ne 0) { throw 'Launcher build failed' }
& $compiler /nologo /target:winexe /platform:x64 /reference:System.Management.dll /out:PACTMaintenance.exe Maintenance.cs
if ($LASTEXITCODE -ne 0) { throw 'Maintenance build failed' }
& $compiler /nologo /target:exe /out:dist\MaintenanceTests.exe tests\MaintenanceTests.cs
if ($LASTEXITCODE -ne 0) { throw 'Installer test build failed' }
& dist\MaintenanceTests.exe (Join-Path $PSScriptRoot 'PACTMaintenance.exe')
if ($LASTEXITCODE -ne 0) { throw 'Installer path tests failed' }
& package\runtime\python.exe tests\test_pact.py
if ($LASTEXITCODE -ne 0) { throw 'PACT tests failed' }
& package\runtime\python.exe tests\test_revision.py
if ($LASTEXITCODE -ne 0) { throw 'PACT revision tests failed' }
& package\runtime\python.exe tests\test_polish.py
if ($LASTEXITCODE -ne 0) { throw 'PACT export and polish tests failed' }
& package\runtime\python.exe tests\test_hover_hydration.py
if ($LASTEXITCODE -ne 0) { throw 'PACT hover and hydration tests failed' }
& package\runtime\python.exe tests\test_v11.py
if ($LASTEXITCODE -ne 0) { throw 'PACT v1.1 tests failed' }
& $InnoCompiler /Q PACT.iss
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' }
Write-Output 'Built dist\PACT_v1.1.0_Setup.exe'
