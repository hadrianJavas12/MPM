Set-Location D:\MPM
$env:CL_MPM_REFERENCE_PNG = '0'
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\triaxial-clay-2d.lisp D:\MPM\output\framework-refactor-2026-10-15\triaxial-2d-after *> D:\MPM\output\framework-refactor-2026-10-15\triaxial-2d-after.log
$nativeExit = $LASTEXITCODE
@{exitCode=$nativeExit; commit='2f6476f'; endedUtc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 D:\MPM\output\framework-refactor-2026-10-15\triaxial-2d-after-status.json
exit $nativeExit

