"""Try to retrieve Windows credentials for PostgreSQL."""
import subprocess

# Use PowerShell to enumerate credential manager
ps_script = r"""
$sig = @'
[DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern bool CredRead(string target, int type, int flags, out IntPtr credential);

[DllImport("advapi32.dll", SetLastError = true)]
public static extern bool CredEnumerate(string filter, int flags, out int count, out IntPtr pCredentials);

[DllImport("advapi32.dll", SetLastError = true)]
public static extern bool CredFree(IntPtr buffer);

public struct CREDENTIAL_ATTRIBUTE {
    public string Keyword;
    public int Flags;
    public int ValueSize;
    public IntPtr Value;
}

public struct CREDENTIAL {
    public int Flags;
    public int Type;
    public string TargetName;
    public string Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public int CredentialBlobSize;
    public IntPtr CredentialBlob;
    public int Persist;
    public int AttributeCount;
    public IntPtr Attributes;
    public string TargetAlias;
    public string UserName;
}
'@

Add-Type -TypeDefinition $sig -PassThru | Out-Null

# Enumerate all credentials
$count = 0
$ptr = [IntPtr]::Zero
$result = [CredEnumerate]::Invoke($null, 0, [ref]$count, [ref]$ptr)
if ($result) {
    $credSize = [System.Runtime.InteropServices.Marshal]::SizeOf([type][CREDENTIAL])
    for ($i = 0; $i -lt $count; $i++) {
        $credPtr = [System.Runtime.InteropServices.Marshal]::ReadIntPtr($ptr, $i * [IntPtr]::Size)
        $cred = [System.Runtime.InteropServices.Marshal]::PtrToStructure($credPtr, [type][CREDENTIAL])
        if ($cred.TargetName -like "*PostgreSQL*" -or $cred.TargetName -like "*pgAdmin*" -or $cred.TargetName -like "*postgres*") {
            Write-Output "Target: $($cred.TargetName)"
            Write-Output "User: $($cred.UserName)"
            if ($cred.CredentialBlob -ne [IntPtr]::Zero) {
                $blob = New-Object byte[] $cred.CredentialBlobSize
                [System.Runtime.InteropServices.Marshal]::Copy($cred.CredentialBlob, $blob, 0, $cred.CredentialBlobSize)
                $password = [System.Text.Encoding]::Unicode.GetString($blob)
                Write-Output "Password: $password"
            }
            Write-Output "---"
        }
    }
    [CredFree]::Invoke($ptr) | Out-Null
}
"""

result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script],
                       capture_output=True, text=True, timeout=30)
print("STDOUT:", result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])
