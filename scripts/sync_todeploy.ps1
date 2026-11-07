# Sync note
#
# A tananyag indexek és az embedding a ToDeploy/data alatt élnek.
# Ez a script már NEM a régi assets/materials mappából másol.
# Frissítéshez a ToDeploy tartalmát kell karbantartani / újra deployolni.

Write-Host "A szerver forrása: ToDeploy/"
Write-Host "Flutter kliens: lib/ + assets/config/app_config.json (cloudBaseUrl)"
Write-Host "Nincs mit syncelni a monorepo assets-ből – cloud-only architektúra."
