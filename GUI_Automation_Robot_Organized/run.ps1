param(
    [string]$Test = "tests\select_board.robot"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

python -m robot --outputdir results $Test
exit $LASTEXITCODE
