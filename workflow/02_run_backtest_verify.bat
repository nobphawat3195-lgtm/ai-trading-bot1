@echo off
REM ================================================================
REM  แก้ 2 บรรทัดนี้ให้ตรงกับเครื่องคุณก่อนรัน
REM ================================================================
set TERMINAL_EXE="C:\Program Files\YOUR_BROKER_MT5\terminal64.exe"
set DATA_FOLDER="C:\Users\YOURNAME\AppData\Roaming\MetaQuotes\Terminal\YOUR_TERMINAL_ID"
REM ================================================================

echo กำลังรัน Backtest ยืนยันผล 1 รอบ (โหมด 1 Minute OHLC) ...
%TERMINAL_EXE% /config:%~dp002_backtest_verify.ini

echo.
echo เสร็จแล้ว ไปหาไฟล์รายงาน SRv441_verify.htm ใน Data Folder\Tester\ หรือ
echo Data Folder\MQL5\Files\Reports\ (ตำแหน่งขยับได้ตามบิลด์ MT5)
echo เทียบตัวเลขกับที่เคยรันผ่าน GUI มาก่อน ถ้าใกล้เคียงกันค่อยไปขั้น 03
pause
