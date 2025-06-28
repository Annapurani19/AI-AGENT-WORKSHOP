@echo off
echo.
echo ✅ Fixing Node.js and npm for React setup...

:: Set manual paths (update if Node.js is installed elsewhere)
set NODE_PATH=C:\Program Files\nodejs

:: Add to PATH temporarily for this session
set PATH=%NODE_PATH%;%PATH%

:: Verify executables exist
if exist "%NODE_PATH%\node.exe" (
    echo 🟢 Node.js found
) else (
    echo 🔴 Node.js NOT found in %NODE_PATH%
    pause
    exit /b
)

if exist "%NODE_PATH%\npm.cmd" (
    echo 🟢 npm found
) else (
    echo 🔴 npm NOT found
    pause
    exit /b
)

if exist "%NODE_PATH%\npx.cmd" (
    echo 🟢 npx found
) else (
    echo 🔴 npx NOT found
    pause
    exit /b
)

:: Show versions
echo.
echo 📦 Node version:
"%NODE_PATH%\node.exe" -v

echo 📦 npm version:
"%NODE_PATH%\npm.cmd" -v

echo 📦 npx version:
"%NODE_PATH%\npx.cmd" -v

:: Change to project folder
cd /d %~dp0

:: Create React app
echo.
echo 🚀 Creating React app in folder: frontend
"%NODE_PATH%\npx.cmd" create-react-app frontend

echo.
echo ✅ All done! Now run:
echo     cd frontend
echo     npm start
pause
