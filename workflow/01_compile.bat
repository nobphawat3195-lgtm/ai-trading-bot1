@echo off
REM ================================================================
REM  แก้ 2 บรรทัดนี้ให้ตรงกับเครื่องคุณก่อนรัน (ดูวิธีหาใน 00_อ่านก่อนเริ่ม.txt)
REM ================================================================
set METAEDITOR_EXE="C:\Program Files\YOUR_BROKER_MT5\metaeditor64.exe"
set DATA_FOLDER="C:\Users\YOURNAME\AppData\Roaming\MetaQuotes\Terminal\YOUR_TERMINAL_ID"
REM ================================================================

echo Compiling XAU_StraddleReverse_v4_40.mq5 ...
%METAEDITOR_EXE% /compile:%DATA_FOLDER%\MQL5\Experts\XAU_StraddleReverse_v4_40.mq5 /log:%DATA_FOLDER%\MQL5\Experts\compile_log.txt

echo.
echo ---- ผลลัพธ์การคอมไพล์ (compile_log.txt) ----
type %DATA_FOLDER%\MQL5\Experts\compile_log.txt
echo.
echo ต้องเห็นคำว่า "0 error(s)" ด้านบน ถ้าไม่เห็น ห้ามรัน 02 ต่อ ส่ง log นี้ให้ Claude ดู
pause
