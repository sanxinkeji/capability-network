# Admin API smoke test — run while backend is up on :8000
$Root = "http://127.0.0.1:8000"
$Base = "$Root/api/v1"
$fail = 0

function Test-Endpoint($Name, $Method, $Url, $Token, $Body) {
  try {
    $headers = @{ Authorization = "Bearer $Token" }
    if ($Method -eq "GET") {
      $r = Invoke-WebRequest -Uri $Url -Headers $headers -UseBasicParsing -TimeoutSec 10
    } else {
      $r = Invoke-WebRequest -Uri $Url -Method $Method -Headers $headers -Body $Body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    }
    if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
      Write-Host "[OK] $Name ($($r.StatusCode))"
    } else {
      Write-Host "[FAIL] $Name status $($r.StatusCode)"
      $script:fail++
    }
  } catch {
    Write-Host "[FAIL] $Name — $($_.Exception.Message)"
    $script:fail++
  }
}

function Test-PublicEndpoint($Name, $Url, $ExpectStatus) {
  try {
    $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
    if ($r.StatusCode -eq $ExpectStatus) {
      Write-Host "[OK] $Name ($($r.StatusCode))"
    } else {
      Write-Host "[FAIL] $Name status $($r.StatusCode), expected $ExpectStatus"
      $script:fail++
    }
  } catch {
    Write-Host "[FAIL] $Name — $($_.Exception.Message)"
    $script:fail++
  }
}

Write-Host "=== Health checks ==="
Test-PublicEndpoint "health" "$Root/health" 200
Test-PublicEndpoint "health-ready" "$Root/health/ready" 200

Write-Host "=== Admin smoke test ==="

try {
  $login = Invoke-RestMethod -Uri "$Base/auth/login" -Method POST -Body '{"account":"admin_qa@test.com","password":"password123"}' -ContentType "application/json"
  $token = $login.data.access_token
  Write-Host "[OK] login"
} catch {
  Write-Host "[FAIL] login — $($_.Exception.Message)"
  exit 1
}

Test-Endpoint "stats" GET "$Base/admin/stats" $token $null
Test-Endpoint "payment-stats" GET "$Base/admin/payment-stats?days=7" $token $null
Test-Endpoint "dashboard" GET "$Base/admin/dashboard?days=7" $token $null
Test-Endpoint "ops-health" GET "$Base/admin/ops-health" $token $null
Test-Endpoint "users" GET "$Base/admin/users?page=1&page_size=5" $token $null
Test-Endpoint "deals" GET "$Base/admin/deals?page=1&page_size=5" $token $null
Test-Endpoint "offers" GET "$Base/admin/offers?page=1&page_size=5" $token $null
Test-Endpoint "intents" GET "$Base/admin/intents?page=1&page_size=5" $token $null
Test-Endpoint "withdrawals" GET "$Base/admin/withdrawals?page=1&page_size=5" $token $null
Test-Endpoint "settings" GET "$Base/admin/settings" $token $null
Test-Endpoint "payment-orders" GET "$Base/admin/payment-orders?page=1&page_size=5" $token $null
Test-Endpoint "announcements" GET "$Base/admin/announcements?page=1&page_size=5" $token $null
Test-Endpoint "ledger" GET "$Base/admin/ledger?page=1&page_size=5" $token $null
Test-Endpoint "audit-logs" GET "$Base/admin/audit-logs?page=1&page_size=5" $token $null
Test-Endpoint "agent-stats" GET "$Base/admin/agent-stats" $token $null
Test-Endpoint "agent-keys" GET "$Base/admin/agent-keys?page=1&page_size=5" $token $null

try {
  $ops = Invoke-RestMethod -Uri "$Base/admin/ops-health" -Headers @{ Authorization = "Bearer $token" }
  $resourceNames = @($ops.data.resources | ForEach-Object { $_.name })
  foreach ($expected in @("数据库", "Redis", "支付通道")) {
    if ($resourceNames -contains $expected) {
      Write-Host "[OK] ops-health resource: $expected"
    } else {
      Write-Host "[FAIL] ops-health missing resource: $expected"
      $script:fail++
    }
  }
} catch {
  Write-Host "[FAIL] ops-health resources — $($_.Exception.Message)"
  $script:fail++
}

Write-Host "=== Done: $fail failure(s) ==="
exit $fail
