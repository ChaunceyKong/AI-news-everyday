param(
    [string]$Time = "09:00",
    [switch]$Uninstall,
    [switch]$RunNow
)

$TaskName = "Feishu_AI_Daily_Push"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ScriptPath = Join-Path $ScriptDir "push_feishu.py"

if ($Uninstall) {
    Write-Host "[*] 正在卸载 Windows 定时任务: $TaskName ..." -ForegroundColor Yellow
    schtasks.exe /Delete /TN $TaskName /F
    Write-Host "[✓] 任务已成功删除！" -ForegroundColor Green
    exit 0
}

if ($RunNow) {
    Write-Host "[*] 立即触发一次任务测试..." -ForegroundColor Cyan
    schtasks.exe /Run /TN $TaskName
    exit 0
}

# 寻找 pythonw.exe 或 python.exe (pythonw 不会弹出黑框命令行窗口)
$PythonCmd = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonCmd) {
    $PythonCmd = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
}

if (-not $PythonCmd) {
    Write-Host "[!] 未检测到系统中的 Python，请确保 Python 已加入 PATH 环境变量。" -ForegroundColor Red
    exit 1
}

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   飞书 AI 每日早报 - Windows 定时任务配置" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName"
Write-Host "每天运行时间: $Time"
Write-Host "Python 路径: $PythonCmd"
Write-Host "执行脚本: $ScriptPath"
Write-Host "工作目录: $ScriptDir"
Write-Host "----------------------------------------------"

# 使用 schtasks.exe 注册每日计划任务
$ActionCmd = "`"$PythonCmd`" `"$ScriptPath`""
$CreateCmd = "schtasks.exe /Create /SC DAILY /TN `"$TaskName`" /TR `"$ActionCmd`" /ST $Time /F"

Invoke-Expression $CreateCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[✓] 每日定时推送任务创建成功！每天将在 $Time 自动推送最新 AI 重点资讯到飞书。" -ForegroundColor Green
    Write-Host "`n常用管理命令：" -ForegroundColor Gray
    Write-Host "  立即测试运行一次: powershell -File setup_windows_task.ps1 -RunNow" -ForegroundColor Gray
    Write-Host "  修改运行时间:     powershell -File setup_windows_task.ps1 -Time 08:30" -ForegroundColor Gray
    Write-Host "  删除该定时任务:   powershell -File setup_windows_task.ps1 -Uninstall" -ForegroundColor Gray
} else {
    Write-Host "`n[!] 创建计划任务失败，请尝试以管理员身份运行 PowerShell 后重试。" -ForegroundColor Red
}
