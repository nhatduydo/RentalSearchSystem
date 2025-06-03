# Load variables from sendgrid.env
$envFile = ".\sendgrid.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "export (\w+)='(.+)'") {
            $name = $matches[1]
            $value = $matches[2]
            [System.Environment]::SetEnvironmentVariable($name, $value, 'Process')
        }
    }
    Write-Host "✅ Environment variables loaded from sendgrid.env"
} else {
    Write-Host "⚠️ File sendgrid.env not found"
}