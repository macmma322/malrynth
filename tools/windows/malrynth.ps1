<#
.SYNOPSIS
    Malrynth Windows Developer CLI Launcher.

.DESCRIPTION
    Thin Windows PowerShell launcher that dispatches to the cross-platform Python core.
    Compatible with Windows PowerShell 5.1 and PowerShell 7+.
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "malrynth.py"

# Locate Python 3
$pythonCmd = $null
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} else {
    Write-Error "Python >= 3.10 is required to run Malrynth developer tools. Install it or add it to PATH."
    exit 1
}

& $pythonCmd $pythonScript @ScriptArgs
exit $LASTEXITCODE
