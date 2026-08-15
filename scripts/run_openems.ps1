# Startet OpenEMS Edge (Simulator-Modus) im Hintergrund.
# Arbeitsverzeichnis data_cache\openems, damit die OSGi-Konfiguration erhalten bleibt.
$ErrorActionPreference = "Stop"

$repo = Split-Path $PSScriptRoot -Parent
$jdk = Get-ChildItem "C:\Program Files\Eclipse Adoptium" -Directory -Filter "jdk-21*" |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $jdk) { throw "Kein JDK 21 unter 'C:\Program Files\Eclipse Adoptium' gefunden." }

$jar = Get-ChildItem "$repo\external\openems" -Recurse -Filter "openems-edge.jar" |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $jar) { throw "openems-edge.jar nicht gefunden - erst bauen: gradlew buildEdge" }

$workDir = "$repo\data_cache\openems"
New-Item -ItemType Directory -Force $workDir | Out-Null

Write-Host "Starte OpenEMS Edge: $jar"
Start-Process -FilePath "$jdk\bin\java.exe" -ArgumentList "-jar", "`"$jar`"" -WorkingDirectory $workDir
Write-Host "Edge laeuft im Hintergrund. Felix-Console: http://localhost:8080/system/console (admin/admin)"
Write-Host "Danach einmalig konfigurieren: .venv\Scripts\python.exe scripts\openems_bootstrap.py"
