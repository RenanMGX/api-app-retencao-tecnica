$exclude = @("venv", "botPython.zip", "#material", "Attachments_Download", "download")
$files = Get-ChildItem -Path . -Exclude $exclude
Compress-Archive -Path $files -DestinationPath "botPython.zip" -Force