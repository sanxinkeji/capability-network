# Agent 竞价室 Phase A 冒烟测试（REST API 全链路）
# 前置：backend http://127.0.0.1:8000，已 alembic upgrade head
# 用法：.\deploy\auction-smoke.ps1
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

function New-AgentOffer {
    param([string]$Token, [string]$Title, [int]$PriceCents)
    $body = @{
        title = $Title
        description = "Auction smoke agent offer $Title"
        category = "design"
        channel = "agent"
        billing_model = "per_use"
        price_cents = $PriceCents
        currency = "CNY"
        delivery_description = "Auto deliver logo preview"
    }
    $offer = Invoke-Api -Method Post -Path "/offers" -Body $body -Token $Token
    $offerId = $offer.data.id
    Invoke-Api -Method Post -Path "/offers/$offerId/publish" -Token $Token | Out-Null
    return $offerId
}

Write-Host "==> Auction smoke test (Phase A)" -ForegroundColor Cyan

Write-Host "`n1. Auth (buyer + 2 sellers)"
$buyerToken = Get-Or-Register -Email "buyer_qa@test.com" -Password "password123" -DisplayName "Buyer QA"
$seller1Token = Get-Or-Register -Email "seller_qa@test.com" -Password "password123" -DisplayName "Seller QA"
$seller2Token = Get-Or-Register -Email "seller2_qa@test.com" -Password "password123" -DisplayName "Seller2 QA"

Write-Host "`n2. Buyer recharge"
try {
    Invoke-Api -Method Post -Path "/wallets/recharge" -Body @{ amount_cents = 10000 } -Token $buyerToken | Out-Null
    Write-Host "  recharged 10000 cents"
} catch {
    Write-Host "  recharge skipped (may already have balance)"
}

Write-Host "`n3. Sellers publish agent offers"
$offer1 = New-AgentOffer -Token $seller1Token -Title "Auction Logo Agent A" -PriceCents 500
$offer2 = New-AgentOffer -Token $seller2Token -Title "Auction Logo Agent B" -PriceCents 480
Write-Host "  offer1=$offer1 offer2=$offer2"

Write-Host "`n4. Buyer create agent intent"
$intentBody = @{
    title = "Logo auction smoke intent"
    description = "Need logo design agent bidding demo"
    category = "design"
    channel = "agent"
    budget_max = 500
    currency = "CNY"
}
$intent = Invoke-Api -Method Post -Path "/intents" -Body $intentBody -Token $buyerToken
$intentId = $intent.data.id
Write-Host "  intent_id=$intentId"

Write-Host "`n5. Matching (optional sanity)"
$match = Invoke-Api -Method Post -Path "/matching/run" -Body @{ intent_id = $intentId; top_n = 5 } -Token $buyerToken
Write-Host "  match candidates: $($match.data.candidates.Count)"

Write-Host "`n6. Agents join auction"
$join1 = Invoke-Api -Method Post -Path "/intents/$intentId/auction/join" -Body @{ offer_id = $offer1 } -Token $seller1Token
$auctionId = $join1.data.id
Write-Host "  after seller1: participants=$($join1.data.participant_count) status=$($join1.data.status)"
$join2 = Invoke-Api -Method Post -Path "/intents/$intentId/auction/join" -Body @{ offer_id = $offer2 } -Token $seller2Token
Write-Host "  after seller2: participants=$($join2.data.participant_count) status=$($join2.data.status)"

if ($join2.data.status -ne "matched") {
    throw "Expected auction status matched, got $($join2.data.status)"
}

Write-Host "`n7. Buyer start auction"
$started = Invoke-Api -Method Post -Path "/intents/$intentId/auction/start" -Token $buyerToken
if ($started.data.status -ne "auctioning") {
    throw "Expected auctioning, got $($started.data.status)"
}
Write-Host "  status=auctioning"

Write-Host "`n8. Agents bid"
$bid1 = Invoke-Api -Method Post -Path "/auctions/$auctionId/bid" -Body @{ amount_cents = 480 } -Token $seller1Token
$bid2 = Invoke-Api -Method Post -Path "/auctions/$auctionId/bid" -Body @{ amount_cents = 450 } -Token $seller2Token
$winBid = ($bid2.data.bids | Sort-Object amount_cents | Select-Object -First 1)
Write-Host "  bids=$($bid2.data.bids.Count) winning_candidate=$($winBid.amount_cents) cents"

Write-Host "`n9. Buyer select + deal"
$selected = Invoke-Api -Method Post -Path "/auctions/$auctionId/select" -Body @{ bid_id = $winBid.id } -Token $buyerToken
$dealId = $selected.data.deal_id
if (-not $dealId) { throw "deal_id missing after select" }
Write-Host "  deal_id=$dealId status=$($selected.data.status)"

Write-Host "`n10. Pay deal"
$paid = Invoke-Api -Method Post -Path "/deals/$dealId/pay" -Token $buyerToken
Write-Host "  deal status after pay: $($paid.data.status)"

Write-Host "`n==> AUCTION SMOKE PASSED" -ForegroundColor Green
Write-Host "  UI: http://127.0.0.1:5173/app/auctions/$intentId"
