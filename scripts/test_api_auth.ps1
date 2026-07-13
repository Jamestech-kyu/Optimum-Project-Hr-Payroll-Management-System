param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$Username,
    [string]$Password
)

if (-not $Username) {
    $Username = Read-Host "Username"
}

if (-not $Password) {
    $Password = Read-Host "Password"
}

$loginBody = @{
    username = $Username
    password = $Password
} | ConvertTo-Json

Write-Host "POST /api/auth/login/"
$login = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/auth/login/" `
    -ContentType "application/json" `
    -Body $loginBody

$accessToken = $login.access
$refreshToken = $login.refresh

if (-not $accessToken) {
    throw "Login did not return an access token."
}

$headers = @{
    Authorization = "Bearer $accessToken"
}

Write-Host "GET /api/auth/me/"
$me = Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/api/auth/me/" `
    -Headers $headers
$me | ConvertTo-Json -Depth 5

Write-Host "GET /api/leave/types/"
Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/api/leave/types/" `
    -Headers $headers | ConvertTo-Json -Depth 5

Write-Host "GET /api/payroll/runs/"
Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/api/payroll/runs/" `
    -Headers $headers | ConvertTo-Json -Depth 5

Write-Host "POST /api/auth/logout/"
$logoutBody = @{
    refresh = $refreshToken
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/auth/logout/" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $logoutBody | ConvertTo-Json -Depth 5
