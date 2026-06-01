@echo off
cd /d "C:\김연아\2026년_AXDX팀\06. AI 툴 제작\01_EZ_Datahub_dashboard"
py trigger_notif.py >> checkpoints\notifier_log.txt 2>&1
