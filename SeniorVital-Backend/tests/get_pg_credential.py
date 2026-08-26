"""Leer las credenciales de pgAdmin desde el Administrador de Credenciales de Windows."""
import subprocess

ps_script = """
$vault = [Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime]::Load()
$creds = $vault.RetrieveAll()
foreach ($cred in $creds) {
    if ($cred.Resource -like "*pgAdmin*") {
        $cred.RetrievePassword()
        Write-Output "Resource: $($cred.Resource)"
        Write-Output "UserName: $($cred.UserName)"
        Write-Output "Password: $($cred.Password)"
    }
}
"""

result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, timeout=15)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr[:500] if result.stderr else "")
