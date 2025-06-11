@echo off
echo 🚀 正在部署到 GitHub Pages...

git add .

git commit -m "Update" 

git push -u origin main

echo 部署完成！🎉
pause
