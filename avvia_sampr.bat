@echo off
rem Sam.Pr Miner - chiude openMSX, aggiorna la ROM e riavvia
set DIR=E:\Dropbox\FAUSTO\SVILUPPI\MSX\EMULATORI\openMSX

taskkill /IM openmsx.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul

if exist "%DIR%\sampr-miner-new.rom" copy /Y "%DIR%\sampr-miner-new.rom" "%DIR%\sampr-miner.rom" >nul

start "" "%DIR%\openmsx.exe" -machine Sony_HB-55P -carta "%DIR%\sampr-miner.rom" -romtype ascii8
