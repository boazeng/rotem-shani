# sync.ps1 — סנכרון הפרויקט מול GitHub בפקודה אחת
#
# מריץ: pull (מביא שינויים מהמחשב השני) -> add -> commit -> push
# שימוש:
#   .\sync.ps1                      # הודעת קומיט אוטומטית עם תאריך/שעה
#   .\sync.ps1 "עדכנתי פלורוסנטים"   # הודעת קומיט משלך
#
# מה זה פותר: לחיצה על 💾 בסימולציה שומרת רק לקובץ המקומי (rotem_saved.json),
# לא לגיטהאב. הסקריפט הזה מעלה את הקובץ (וכל שאר השינויים) לריפו, כדי
# שהמחשב השני יקבל אותם ב-git pull.

param([string]$Message = "")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# ודא ש-Git LFS מותקן (קבצי ה-.glb תלויים בו)
if (-not (Get-Command git-lfs -ErrorAction SilentlyContinue)) {
    Write-Host "⚠  Git LFS לא מותקן. התקן: https://git-lfs.com  ואז הרץ: git lfs install" -ForegroundColor Yellow
    exit 1
}

Write-Host "→ מביא שינויים מהריפו (pull)..." -ForegroundColor Cyan
git pull --no-edit

# יש בכלל מה לשמור?
$changes = git status --porcelain
if (-not $changes) {
    Write-Host "✓ אין שינויים מקומיים — הריפו כבר מעודכן." -ForegroundColor Green
    exit 0
}

Write-Host "→ שינויים שיועלו:" -ForegroundColor Cyan
git -c core.quotepath=off status --short

if (-not $Message) {
    $Message = "עדכון פריסה — " + (Get-Date -Format "yyyy-MM-dd HH:mm")
}

git add -A
git commit -m $Message
Write-Host "→ מעלה לריפו (push, כולל LFS)..." -ForegroundColor Cyan
git push

Write-Host "✓ הועלה בהצלחה. המחשב השני יקבל את זה עם: git pull" -ForegroundColor Green
