@echo off
title EZ데이터허브 자동 동기화 프로그램
echo ======================================================
echo  데이터 동기화 및 위험 감지 알림을 시작합니다...
echo  실행 시간: %date% %time%
echo ======================================================

:: 1. 프로젝트 폴더로 이동 (절대 경로 사용)
cd /d "c:\김연아\Antigravity\현황대시보드"

:: 실제 파이썬 경로 설정
set PYTHON_EXE="C:\Users\EZPMP\AppData\Local\Python\pythoncore-3.14-64\python.exe"

:: 2. 데이터 수집기(collector.py) 실행
echo [1/2] 구글 시트 데이터 수집 중...
%PYTHON_EXE% "자동화 py\collector.py"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 데이터 수집 중 문제가 발생했습니다. 작업을 중단합니다.
    echo 실행 시간: %date% %time%
    timeout /t 10
    exit /b %ERRORLEVEL%
)

:: 3. 이메일 알림 체크
echo [2/2] 위험 인원 감지 및 이메일 알림 체크 중...
%PYTHON_EXE% "trigger_notif.py"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 알림 체크 중 문제가 발생했습니다.
    timeout /t 10
    exit /b %ERRORLEVEL%
)

echo ======================================================
echo  모든 동기화 및 알림 작업이 성공적으로 완료되었습니다. (%date% %time%)
echo ======================================================
timeout /t 5
