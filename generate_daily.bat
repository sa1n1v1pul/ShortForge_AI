@echo off
echo ╔═══════════════════════════════════════════╗
echo ║  🎬 ShortForge AI — Daily Video Generator  ║
echo ╚═══════════════════════════════════════════╝
echo.

cd /d D:\ShortForge-AI

echo Generating 5 videos...
echo.

"C:\Users\dream\AppData\Local\Programs\Python\Python312\python.exe" main.py --niche amazing_facts --count 5 --lang english

echo.
echo ═══════════════════════════════════════════
echo   Done! Check D:\ShortForge-AI\output\
echo ═══════════════════════════════════════════
pause
