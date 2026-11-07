# Resolves flutter.bat for this project (beta SDK with native assets).
# Priority: $env:FLUTTER_SDK -> C:\flutter-beta\flutter -> PATH

$ErrorActionPreference = "Stop"

function Get-ProjectFlutter {
    param([string]$ScriptRoot)

    $candidates = @()
    if ($env:FLUTTER_SDK) {
        $candidates += (Join-Path $env:FLUTTER_SDK "bin\flutter.bat")
    }
    $candidates += "C:\flutter-beta\flutter\bin\flutter.bat"
    $candidates += "C:\flutter\flutter\bin\flutter.bat"

    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) {
            return (Resolve-Path $c).Path
        }
    }

    if (Test-Path "C:\flutter-beta\flutter\bin\flutter.bat") {
        $env:FLUTTER_SDK = "C:\flutter-beta\flutter"
    }

    $cmd = Get-Command flutter -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    return $null
}

function Test-NativeAssetsAvailable {
    param([string]$FlutterBat)

    $cfg = & $FlutterBat config --list 2>&1 | Out-String
    if ($cfg -match "enable-native-assets:\s*true\s*\(Unavailable\)") {
        return $false
    }
    if ($cfg -match "enable-native-assets:\s*false") {
        & $FlutterBat config --enable-native-assets | Out-Null
    }
    return $true
}

function Ensure-FlutterForGemmaBuild {
    param([string]$ScriptRoot)

    $flutterBat = Get-ProjectFlutter -ScriptRoot $ScriptRoot
    if (-not $flutterBat) {
        Write-Host "HIBA: flutter nem talalhato." -ForegroundColor Red
        Write-Host "Futtasd: powershell -ExecutionPolicy Bypass -File scripts\setup_flutter_beta_windows.ps1"
        exit 1
    }

    $version = & $flutterBat --version 2>&1 | Select-Object -First 1
    Write-Host "Flutter: $flutterBat" -ForegroundColor DarkGray
    Write-Host "         $version" -ForegroundColor DarkGray

    if (-not (Test-NativeAssetsAvailable -FlutterBat $flutterBat)) {
        Write-Host ""
        Write-Host "HIBA: Ez a Flutter SDK nem tamogatja a native assets-et (flutter_gemma 1.0 kell)." -ForegroundColor Red
        Write-Host ""
        Write-Host "Ne hasznald: flutter channel beta  (Windows-on gyakran Filename too long hiba)" -ForegroundColor Yellow
        Write-Host "Helyette futtasd egyszer:" -ForegroundColor Yellow
        Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\setup_flutter_beta_windows.ps1"
        Write-Host ""
        Write-Host "Reszletek: docs/FLUTTER_GEMMA_SETUP.md"
        exit 1
    }

    return $flutterBat
}
