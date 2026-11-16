param([Parameter(Mandatory=$true)][string]$Package,
      [string]$Python = 'python',
      [string]$ArchiveParent = 'C:\Users\tetsu\Dev-Artifact-Archive\Hachibei-Lab\PR-30')
$ErrorActionPreference = 'Stop'
# Run from a new PowerShell process. No ExecutionPolicy or environment changes.
$Expected = '47e7e14bad9964f6168142a579f2814c00816f9bfd940bcdcfb9d84756378bcc'
if ((Get-Item -LiteralPath $Package).Length -ne 1679175) { throw 'ZIP size mismatch' }
if ((Get-FileHash -LiteralPath $Package -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Expected) { throw 'ZIP SHA mismatch' }
$Destination = Join-Path $ArchiveParent ('archive-' + [guid]::NewGuid().ToString())
& $Python (Join-Path $PSScriptRoot 'verify_archive.py') --package $Package --destination $Destination
if ($LASTEXITCODE -ne 0) { throw 'Archive verification BLOCKED; retain partial directory, do not retry into it' }
Write-Output ('Archive receipt: ' + (Join-Path $Destination 'windows-readback.json'))
