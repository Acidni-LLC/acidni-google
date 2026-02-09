<#
.SYNOPSIS
    Acidni Google Helper — PowerShell wrapper for Google Analytics 4 operations.

.DESCRIPTION
    Provides the [AcidniGoogle] class for managing GA4 accounts, properties,
    data streams, and reports. Wraps google-cli.py via Python subprocess calls.

    Credentials are loaded automatically from Azure Key Vault (kv-terprint-dev)
    using the ga4-service-account-json secret.

.EXAMPLE
    . "C:\Users\JamiesonGill\Documents\GitHub\Acidni-LLC\acidni-google\google-helper.ps1"
    $ga = [AcidniGoogle]::new()

    # List all accounts
    $ga.ListAccounts()

    # List all properties
    $ga.ListProperties()

    # List data streams for a property
    $ga.ListStreams("123456789")

    # Run a report
    $ga.RunReport("123456789", "7daysAgo", "today")
    $ga.RunReport("123456789", "2026-01-01", "2026-02-07", "activeUsers,sessions", "date")

    # Create property with web stream
    $ga.CreateProperty("My Product", "123456789", "https://myproduct.acidni.net")

    # Create data stream
    $ga.CreateStream("123456789", "My Product Web", "https://myproduct.acidni.net")

    # Store measurement ID in Key Vault
    $ga.StoreMeasurementId("myproduct-ga4-measurement-id", "G-XXXXXXXXXX")
#>

class AcidniGoogle {
    [string]$CliPath
    [string]$PythonExe

    # Default constructor
    AcidniGoogle() {
        $this.CliPath = "C:\Users\JamiesonGill\Documents\GitHub\Acidni-LLC\acidni-google\google-cli.py"
        $this.PythonExe = "python"

        if (-not (Test-Path $this.CliPath)) {
            throw "google-cli.py not found at: $($this.CliPath)"
        }
        Write-Host "Acidni Google Helper loaded. Use `$ga.ListAccounts(), `$ga.ListProperties(), etc." -ForegroundColor Cyan
    }

    # Constructor with custom paths
    AcidniGoogle([string]$CliPath, [string]$PythonExe) {
        $this.CliPath = $CliPath
        $this.PythonExe = $PythonExe

        if (-not (Test-Path $this.CliPath)) {
            throw "google-cli.py not found at: $($this.CliPath)"
        }
        Write-Host "Acidni Google Helper loaded (custom paths)." -ForegroundColor Cyan
    }

    # -------------------------------------------------------------------
    # Internal: Run a CLI command and return parsed JSON
    # -------------------------------------------------------------------
    [object] RunCli([string[]]$Arguments) {
        $allArgs = @($this.CliPath) + $Arguments
        $output = & $this.PythonExe @allArgs 2>&1

        # Separate stdout from stderr
        $stdout = ($output | Where-Object { $_ -is [string] -or $_.GetType().Name -eq 'String' }) -join "`n"
        $stderr = ($output | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] }) | ForEach-Object { $_.ToString() }

        if ($LASTEXITCODE -ne 0) {
            $errMsg = if ($stderr) { $stderr -join "`n" } else { $stdout }
            throw "Google CLI error: $errMsg"
        }

        if ([string]::IsNullOrWhiteSpace($stdout)) {
            return @()
        }

        try {
            return $stdout | ConvertFrom-Json
        }
        catch {
            # If not JSON, return raw string
            return $stdout
        }
    }

    # -------------------------------------------------------------------
    # Account operations
    # -------------------------------------------------------------------
    [object] ListAccounts() {
        return $this.RunCli(@("list-accounts"))
    }

    # -------------------------------------------------------------------
    # Property operations
    # -------------------------------------------------------------------
    [object] ListProperties() {
        return $this.RunCli(@("list-properties"))
    }

    [object] GetProperty([string]$PropertyId) {
        return $this.RunCli(@("get-property", $PropertyId))
    }

    # Create property without URL
    [object] CreateProperty([string]$DisplayName, [string]$AccountId) {
        return $this.RunCli(@("create-property", $DisplayName, $AccountId))
    }

    # Create property with URL (auto-creates web data stream)
    [object] CreateProperty([string]$DisplayName, [string]$AccountId, [string]$Url) {
        return $this.RunCli(@("create-property", $DisplayName, $AccountId, "--url", $Url))
    }

    [object] DeleteProperty([string]$PropertyId) {
        return $this.RunCli(@("delete-property", $PropertyId))
    }

    # -------------------------------------------------------------------
    # Data stream operations
    # -------------------------------------------------------------------
    [object] ListStreams([string]$PropertyId) {
        return $this.RunCli(@("list-streams", $PropertyId))
    }

    [object] CreateStream([string]$PropertyId, [string]$DisplayName, [string]$Url) {
        return $this.RunCli(@("create-stream", $PropertyId, $DisplayName, $Url))
    }

    # -------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------

    # Basic report (default metrics)
    [object] RunReport([string]$PropertyId, [string]$StartDate, [string]$EndDate) {
        return $this.RunCli(@("run-report", $PropertyId, $StartDate, $EndDate))
    }

    # Report with custom metrics
    [object] RunReport([string]$PropertyId, [string]$StartDate, [string]$EndDate, [string]$Metrics) {
        return $this.RunCli(@("run-report", $PropertyId, $StartDate, $EndDate, "--metrics", $Metrics))
    }

    # Report with custom metrics AND dimensions
    [object] RunReport([string]$PropertyId, [string]$StartDate, [string]$EndDate, [string]$Metrics, [string]$Dimensions) {
        return $this.RunCli(@("run-report", $PropertyId, $StartDate, $EndDate, "--metrics", $Metrics, "--dimensions", $Dimensions))
    }

    # -------------------------------------------------------------------
    # Custom dimensions, metrics, audiences
    # -------------------------------------------------------------------
    [object] ListCustomDimensions([string]$PropertyId) {
        return $this.RunCli(@("list-custom-dimensions", $PropertyId))
    }

    [object] ListCustomMetrics([string]$PropertyId) {
        return $this.RunCli(@("list-custom-metrics", $PropertyId))
    }

    [object] ListAudiences([string]$PropertyId) {
        return $this.RunCli(@("list-audiences", $PropertyId))
    }

    # -------------------------------------------------------------------
    # Key Vault operations
    # -------------------------------------------------------------------
    [void] StoreMeasurementId([string]$SecretName, [string]$MeasurementId) {
        az keyvault secret set --vault-name kv-terprint-dev --name $SecretName --value $MeasurementId | Out-Null
        Write-Host "Stored $MeasurementId in Key Vault as $SecretName" -ForegroundColor Green
    }

    [string] GetMeasurementId([string]$SecretName) {
        $val = az keyvault secret show --vault-name kv-terprint-dev --name $SecretName --query value -o tsv
        return $val
    }

    # -------------------------------------------------------------------
    # Convenience: Full product GA4 setup
    # -------------------------------------------------------------------
    [object] SetupProduct([string]$ProductName, [string]$AccountId, [string]$Url, [string]$KvSecretName) {
        Write-Host "`nSetting up GA4 for $ProductName..." -ForegroundColor Yellow

        # Create property with web stream
        $result = $this.CreateProperty($ProductName, $AccountId, $Url)
        Write-Host "  Property created: $($result.name)" -ForegroundColor Green

        if ($result.stream -and $result.stream.measurementId) {
            $mid = $result.stream.measurementId
            Write-Host "  Measurement ID: $mid" -ForegroundColor Green

            # Store in Key Vault
            $this.StoreMeasurementId($KvSecretName, $mid)
            Write-Host "  Stored in Key Vault: $KvSecretName" -ForegroundColor Green
        }
        else {
            Write-Host "  Warning: No measurement ID returned. Create stream manually." -ForegroundColor Yellow
        }

        return $result
    }
}

Write-Host "Acidni Google Helper loaded. Create instance: `$ga = [AcidniGoogle]::new()" -ForegroundColor Cyan
