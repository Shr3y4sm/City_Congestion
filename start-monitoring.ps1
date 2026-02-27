# Start Monitoring - PowerShell Helper
# =====================================
# Easily start traffic monitoring from PowerShell

param(
    [string]$Origin = "Koramangala, Bangalore",
    [string]$Destination = "MG Road, Bangalore"
)

$apiUrl = "http://localhost:8000/start-monitoring"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  CityFlow AI - Start Monitoring" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "Route: " -NoNewline -ForegroundColor Yellow
Write-Host "$Origin → $Destination" -ForegroundColor White

Write-Host "`nStarting monitoring..." -ForegroundColor Yellow

$body = @{
    origin      = $Origin
    destination = $Destination
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5
    
    Write-Host "`n✓ Monitoring started successfully!" -ForegroundColor Green
    Write-Host "  Origin:      $($response.origin)" -ForegroundColor White
    Write-Host "  Destination: $($response.destination)" -ForegroundColor White
    Write-Host "  Interval:    $($response.poll_interval_seconds) seconds" -ForegroundColor White
    
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Run: python watch_traffic.py" -ForegroundColor White
    Write-Host "  2. Or open dashboard: http://localhost:8501" -ForegroundColor White
    Write-Host "================================================================`n" -ForegroundColor Cyan
    
}
catch {
    Write-Host "`n✗ Failed to start monitoring!" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check if API service is running: python api/live_stream.py" -ForegroundColor White
    Write-Host "  2. Verify port 8000 is not blocked" -ForegroundColor White
    Write-Host "  3. Check service status: http://localhost:8000/" -ForegroundColor White
    
    exit 1
}
