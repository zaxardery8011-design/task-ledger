#Requires -Version 5.1
<#
.SYNOPSIS
  Slice-2 sanitization hard gate wrapper (Python regex scan).
#>
param(
  [string]$Root = "",
  [switch]$SoftFail
)
$ErrorActionPreference = "Stop"
if (-not $Root) {
  $Root = Split-Path -Parent $PSScriptRoot
}
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { throw "python not found on PATH" }
$gate = Join-Path $PSScriptRoot "sanitize_gate.py"
$args = @($gate, "--root", $Root)
if ($SoftFail) { $args += "--soft-fail" }
& $py.Source @args
exit $LASTEXITCODE
