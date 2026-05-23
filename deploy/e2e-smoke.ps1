# E2E smoke test: full buy/sell flow via REST API
# 前置条件：backend 已启动（默认 http://127.0.0.1:8000），PostgreSQL 可用。
# 用法：在项目根目录执行 .\deploy\e2e-smoke.ps1
$ErrorActionPreference = "Stop"
$Base = "http://127.0.0.1:8000/api/v1"

function Invoke-Api {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [string]$Token = $null
    )
    $headers = @{ "Content-Type" = "application/json" }
    if ($Token) { $headers["Authorization"] = "Bearer $Token" }
    $uri = "$Base$Path"
    if ($Body) {
        $json = $Body | ConvertTo-Json -Depth 6 -Compress
        return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers -Body $json
    }
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
}

function Get-Or-Register {
    param([string]$Email, [string]$Password, [string]$DisplayName)
    $loginBody = @{ account = $Email; password = $Password }
    try {
        $r = Invoke-Api -Method Post -Path "/auth/login" -Body $loginBody
        Write-Host "  [login] $Email OK"
        return $r.data.access_token
    } catch {
        $regBody = @{ email = $Email; password = $Password; display_name = $DisplayName }
        $r = Invoke-Api -Method Post -Path "/auth/register" -Body $regBody
        Write-Host "  [register] $Email OK"
        return $r.data.access_token
    }
}

Write-Host "==> E2E smoke test" -ForegroundColor Cyan

Write-Host "`n1. Auth (buyer + seller)"
$buyerToken = Get-Or-Register -Email "buyer_qa@test.com" -Password "password123" -DisplayName "Buyer QA"
$sellerToken = Get-Or-Register -Email "seller_qa@test.com" -Password "password123" -DisplayName "Seller QA"

Write-Host "`n2. Buyer recharge 10000 cents"
$recharge = Invoke-Api -Method Post -Path "/wallets/recharge" -Body @{ amount_cents = 10000 } -Token $buyerToken
Write-Host "  balance_available: $($recharge.data.wallet.balance_available)"

Write-Host "`n3. Seller create + publish offer"
$offerBody = @{
    title = "Logo design professional service"
    description = "High quality logo design brand visual design with source files"
    category = "design"
    channel = "human"
    billing_model = "per_use"
    price_cents = 10000
    currency = "CNY"
    delivery_description = "Deliver PNG and SVG source files"
}
$offer = Invoke-Api -Method Post -Path "/offers" -Body $offerBody -Token $sellerToken
$offerId = $offer.data.id
Invoke-Api -Method Post -Path "/offers/$offerId/publish" -Token $sellerToken | Out-Null
Write-Host "  offer_id: $offerId (published)"

Write-Host "`n4. Buyer create intent"
$intentBody = @{
    title = "Need logo design"
    description = "Looking for logo design designer for brand identity"
    category = "design"
    channel = "human"
    budget_max = 10000
    currency = "CNY"
}
$intent = Invoke-Api -Method Post -Path "/intents" -Body $intentBody -Token $buyerToken
$intentId = $intent.data.id
Write-Host "  intent_id: $intentId"

Write-Host "`n5. Run matching"
$match = Invoke-Api -Method Post -Path "/matching/run" -Body @{ intent_id = $intentId; top_n = 5 } -Token $buyerToken
$candidates = $match.data.candidates
if (-not $candidates -or $candidates.Count -eq 0) {
    throw "No match candidates"
}
$matchLogId = $candidates[0].match_log_id
$offerIdFromMatch = $candidates[0].offer_id
if (-not $matchLogId) {
    throw "match_log_id missing from match candidate — ensure backend is running latest code (restart uvicorn if needed)"
}
Write-Host "  candidates: $($candidates.Count), top score: $($candidates[0].match_score), match_log_id: $matchLogId, offer_id: $offerIdFromMatch"

Write-Host "`n6. Create deal + pay (via match_log_id)"
$dealBody = @{ match_log_id = $matchLogId }
$deal = Invoke-Api -Method Post -Path "/deals" -Body $dealBody -Token $buyerToken
$dealId = $deal.data.id
Write-Host "  deal_id: $dealId status: $($deal.data.status)"
$paid = Invoke-Api -Method Post -Path "/deals/$dealId/pay" -Token $buyerToken
Write-Host "  after pay: $($paid.data.status)"

Write-Host "`n7. Seller deliver"
$delivered = Invoke-Api -Method Post -Path "/deals/$dealId/deliver" -Body @{ text = "Delivered logo design v1" } -Token $sellerToken
Write-Host "  after deliver: $($delivered.data.status)"

Write-Host "`n8. Buyer confirm"
$confirmed = Invoke-Api -Method Post -Path "/deals/$dealId/confirm" -Body @{} -Token $buyerToken
Write-Host "  final status: $($confirmed.data.status)"

Write-Host "`n9. Verify wallets and lists"
$buyerWallet = Invoke-Api -Method Get -Path "/wallets/me" -Token $buyerToken
$sellerWallet = Invoke-Api -Method Get -Path "/wallets/me" -Token $sellerToken
$deals = Invoke-Api -Method Get -Path "/deals?page=1&page_size=10" -Token $buyerToken
$ledger = Invoke-Api -Method Get -Path "/wallets/ledger?page=1&page_size=5" -Token $buyerToken

Write-Host "  buyer available: $($buyerWallet.data.balance_available), frozen: $($buyerWallet.data.balance_frozen)"
Write-Host "  seller available: $($sellerWallet.data.balance_available) (expect ~9000 after 10pct fee)"
Write-Host "  deals count: $($deals.data.items.Count)"
Write-Host "  ledger entries: $($ledger.data.items.Count)"

if ($confirmed.data.status -ne "completed") { throw "Deal not completed: $($confirmed.data.status)" }
if ($buyerWallet.data.balance_frozen -ne 0) { throw "Buyer still has frozen funds" }

Write-Host "`n==> E2E PASSED" -ForegroundColor Green
