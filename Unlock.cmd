@ECHO OFF

if "[%1]" == "[49127c4b-02dc-482e-ac4f-ec4d659b7547]" goto :START_PROCESS
set command="""%~f0""" 49127c4b-02dc-482e-ac4f-ec4d659b7547
powershell -NoProfile Start-Process -FilePath '%COMSPEC%' -ArgumentList '/c """%command%"""' -Verb RunAs 2>NUL
goto :EOF

:START_PROCESS

powershell Set-ExecutionPolicy RemoteSigned
echo PowerShell 解鎖完成...

pause
