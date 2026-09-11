Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  FACEVAULT SENTINEL PLATFORM - LOCAL SERVER" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Local URL: http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Default Credentials:" -ForegroundColor Yellow
Write-Host "  Super Admin: superadmin / admin123" -ForegroundColor White
Write-Host "  Operator:    operator   / operator123" -ForegroundColor White
Write-Host ""
Write-Host "Starting server..." -ForegroundColor DarkGray
python main.py
