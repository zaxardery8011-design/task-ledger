#Requires -Version 5.1
<#
.SYNOPSIS
  Optional PS filesystem queue helpers (inbox/processing/outbox).
  Prefer Python package for new integrations.
#>

function Get-TaskLedgerRoot {
  param([string]$Root = "")
  if ($Root) { return $Root.TrimEnd('\', '/') }
  if ($env:TASK_LEDGER_ROOT) { return $env:TASK_LEDGER_ROOT.TrimEnd('\', '/') }
  if ($env:TASK_CORE_ROOT) { return $env:TASK_CORE_ROOT.TrimEnd('\', '/') }
  return (Join-Path (Get-Location) ".task-ledger")
}

function Initialize-TaskLedgerDirs {
  param([string]$Root = "")
  $r = Get-TaskLedgerRoot -Root $Root
  foreach ($name in @("inbox", "processing", "outbox", "ledger", "resume", "flags", "followups", "promises")) {
    $p = Join-Path $r $name
    if (-not (Test-Path -LiteralPath $p)) {
      New-Item -ItemType Directory -Force -Path $p | Out-Null
    }
  }
  return $r
}

function New-TaskLedgerWorkOrder {
  param(
    [Parameter(Mandatory = $true)][string]$Instruction,
    [string]$Root = "",
    [string]$Origin = "operator"
  )
  $r = Initialize-TaskLedgerDirs -Root $Root
  if (Test-Path -LiteralPath (Join-Path $r "flags\ORDER_OFF.flag")) {
    return [pscustomobject]@{ ok = $false; reason = "order_hard_path_off" }
  }
  $stamp = Get-Date -Format "yyyyMMddHHmmss"
  $ms = Get-Date -Format "fff"
  $tid = "task-{0}{1}" -f $stamp, $ms
  $path = Join-Path $r ("inbox\{0}.json" -f $tid)
  $body = [ordered]@{
    schema      = "task_ledger.work_order.v1"
    task_id     = $tid
    instruction = $Instruction.Trim()
    kind        = "task"
    origin      = $Origin
    enqueued_at = (Get-Date).ToUniversalTime().ToString("o")
  }
  $json = ($body | ConvertTo-Json -Depth 6)
  [System.IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))
  return [pscustomobject]@{
    ok      = $true
    task_id = $tid
    path    = $path
    reply   = ("Queued, task_id={0}, will report when done." -f $tid)
  }
}
