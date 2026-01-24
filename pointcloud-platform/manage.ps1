# ============================================================================
# Point Cloud Visualization Platform - Quick Start Script
# ============================================================================
# This script provides easy commands to manage the platform
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "Point Cloud Visualization Platform - Management Script" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

function Show-Menu {
    Write-Host "Available Commands:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Start Platform       - Start all containers" -ForegroundColor Yellow
    Write-Host "  2. Stop Platform        - Stop all containers" -ForegroundColor Yellow
    Write-Host "  3. Restart Platform     - Restart all containers" -ForegroundColor Yellow
    Write-Host "  4. View Logs            - Show container logs" -ForegroundColor Yellow
    Write-Host "  5. View Status          - Show container status" -ForegroundColor Yellow
    Write-Host "  6. Rebuild Containers   - Rebuild and restart" -ForegroundColor Yellow
    Write-Host "  7. Clean Up             - Remove containers and volumes" -ForegroundColor Yellow
    Write-Host "  8. Open Frontend        - Open browser to frontend" -ForegroundColor Yellow
    Write-Host "  9. Open API Docs        - Open browser to API documentation" -ForegroundColor Yellow
    Write-Host "  0. Exit" -ForegroundColor Yellow
    Write-Host ""
}

function Start-Platform {
    Write-Host "Starting platform..." -ForegroundColor Green
    docker-compose up -d
    Write-Host ""
    Write-Host "✓ Platform started!" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:8081" -ForegroundColor Cyan
    Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

function Stop-Platform {
    Write-Host "Stopping platform..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✓ Platform stopped!" -ForegroundColor Green
}

function Restart-Platform {
    Write-Host "Restarting platform..." -ForegroundColor Yellow
    docker-compose restart
    Write-Host "✓ Platform restarted!" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    docker-compose logs -f
}

function Show-Status {
    Write-Host "Container Status:" -ForegroundColor Cyan
    docker-compose ps
    Write-Host ""
    Write-Host "Volume Status:" -ForegroundColor Cyan
    docker volume ls | Select-String "pointcloud"
}

function Rebuild-Platform {
    Write-Host "Rebuilding platform..." -ForegroundColor Yellow
    docker-compose down
    docker-compose build
    docker-compose up -d
    Write-Host "✓ Platform rebuilt and started!" -ForegroundColor Green
}

function Clean-Platform {
    Write-Host "WARNING: This will remove all containers and volumes!" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -eq "yes") {
        docker-compose down -v
        Write-Host "✓ Platform cleaned!" -ForegroundColor Green
    } else {
        Write-Host "Cancelled." -ForegroundColor Yellow
    }
}

function Open-Frontend {
    Write-Host "Opening frontend..." -ForegroundColor Cyan
    Start-Process "http://localhost:8081"
}

function Open-APIDocs {
    Write-Host "Opening API documentation..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000/docs"
}

# Main loop
while ($true) {
    Show-Menu
    $choice = Read-Host "Enter your choice (0-9)"
    
    switch ($choice) {
        "1" { Start-Platform }
        "2" { Stop-Platform }
        "3" { Restart-Platform }
        "4" { Show-Logs }
        "5" { Show-Status }
        "6" { Rebuild-Platform }
        "7" { Clean-Platform }
        "8" { Open-Frontend }
        "9" { Open-APIDocs }
        "0" { 
            Write-Host "Goodbye!" -ForegroundColor Green
            exit 
        }
        default { 
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red 
        }
    }
    
    Write-Host ""
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Clear-Host
}
