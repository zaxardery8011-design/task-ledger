#Requires -Version 5.1
<#
.SYNOPSIS
  Optional PowerShell adapter surface for order classification.
  Core algorithms live in the Python package; this file mirrors classify contracts
  for hosts that still call PS. Not required for pip install / selftests.
.NOTES
  Root via $env:TASK_LEDGER_ROOT or -Root. No private machine paths.
#>

function Resolve-TaskLedgerOrderClass {
  param(
    [Parameter(Mandatory = $true)][string]$Text
  )
  $t = if ($null -eq $Text) { "" } else { $Text.Trim() }
  $out = [ordered]@{
    kind           = "chat"
    note           = ""
    should_enqueue = $false
    needs_confirm  = $false
  }
  if ([string]::IsNullOrWhiteSpace($t)) {
    $out.note = "empty"
    return [pscustomobject]$out
  }
  if ($t -match '(?i)(^\s*stop\b|^\s*halt\b|^\s*停\s*$|停止全部)') {
    $out.kind = "stop"; $out.note = "stop_order"; return [pscustomobject]$out
  }
  if ($t -match '(?i)^(ok|okay|好|好的|收到|了解|嗯|繼續|继续|go)[\s!！。\.]*$') {
    $out.kind = "vague_ack"; $out.note = "vague_ack_not_auth"; return [pscustomobject]$out
  }
  if ($t -match '(?i)(進度呢|進度表|status|現況|做到哪|到哪了|\bprogress\b|\bqueue\b)') {
    $out.kind = "status_probe"; $out.note = "status_or_progress_query"; return [pscustomobject]$out
  }
  if ($t -match '^(確認|是|對|做吧|confirm)[\s!！。\.]*$') {
    $out.kind = "confirm"; $out.should_enqueue = $true; $out.note = "explicit_confirm"
    return [pscustomobject]$out
  }
  $execPat = '(?i)^(請|然后|然後|再)?(立刻|馬上|現在|先|再)?(修|查|做|派|蓋|清|寫|改|實作|執行|开始|開始|繼續|继续|準備|推进|推進|fix|build|write|create)'
  if ($t -match $execPat -or $t -match '(?i)(下一刀|next knife|command-must-become)') {
    $out.kind = "execution_order"; $out.should_enqueue = $true; $out.note = "imperative_work_verb"
    return [pscustomobject]$out
  }
  $out.note = "normal_chat"
  return [pscustomobject]$out
}

function Test-TaskLedgerDeferredPromise {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  $t = $Text.Trim()
  if ($t -match '(?i)(Queued,\s*task_id=|work order queued:\s*task_id=)') { return $false }
  if ($t -match '(?i)(docs[/\\]|outbox|LastWriteTime|## |\d+%)') { return $false }
  if ($t -match '(?i)(let me check|i will check|checking\b|will report|我去查|我來查|稍後回報)') {
    return $true
  }
  return $false
}
