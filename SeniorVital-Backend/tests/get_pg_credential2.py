"""Leer credenciales del Administrador de Credenciales de Windows usando
el módulo credentialmanager o cmdkey.
"""
import subprocess
import os

# Try using cmdkey to list and then read specific credential
# First, let's try a direct approach using PowerShell's credential manager

ps_script = """
Add-Type -AssemblyName System.Security
$cred = [System.Net.CredentialCache]::DefaultCredentials
# Actually, let's use the vault cmdlet
try {
    $cred = Get-StoredCredential -Target "pgAdmin4" -ErrorAction Stop
    Write-Output "Resource: $($cred.Resource)"
    Write-Output "UserName: $($cred.UserName)"
    Write-Output "Password: $($cred.GetNetworkCredential().Password)"
} catch {
    Write-Output "Get-StoredCredential failed: $_"
}
"""

result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, timeout=15)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr[:500] if result.stderr else "")
