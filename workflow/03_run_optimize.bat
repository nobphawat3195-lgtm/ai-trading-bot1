@echo off
REM ================================================================
REM  แก้ 2 บรรทัดนี้ให้ตรงกับเครื่องคุณก่อนรัน
REM ================================================================
set TERMINAL_EXE="C:\Program Files\YOUR_BROKER_MT5\terminal64.exe"
set DATA_FOLDER="C:\Users\YOURNAME\AppData\Roaming\MetaQuotes\Terminal\YOUR_TERMINAL_ID"
REM ================================================================

echo กำลังรัน Optimization (Slow complete algorithm) ...
echo ใช้เวลานาน รันทิ้งไว้ข้ามคืนได้ เทอร์มินัลจะปิดเองเมื่อเสร็จ
%TERMINAL_EXE% /config:%~dp003_optimize.ini

echo.
echo เสร็จแล้ว ไปหาไฟล์ SRv441_optimize.xml (หรือ .htm) ใน Data Folder\Tester\
echo ส่งไฟล์นั้นกลับมาให้ Claude ดูต่อ
pause
