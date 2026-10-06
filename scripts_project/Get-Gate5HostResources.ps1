param([Parameter(Mandatory=$true)][string]$OutputPath,[int]$WatchSeconds=0)
$ErrorActionPreference='Stop'
# Read-only resource probe. No command lines, environment variables, credentials or licences.
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Gate5Memory {
 [StructLayout(LayoutKind.Sequential)] public struct M { public uint length,load; public ulong total,available,pageTotal,pageAvailable,virtualTotal,virtualAvailable,extended; }
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool GlobalMemoryStatusEx(ref M value);
 public static M Read(){ M x=new M(); x.length=(uint)Marshal.SizeOf(typeof(M)); if(!GlobalMemoryStatusEx(ref x)) throw new Exception("GlobalMemoryStatusEx failed"); return x; }
}
'@
function Sample {
 $m=[Gate5Memory]::Read()
 [ordered]@{observed_at=[DateTime]::UtcNow.ToString('o');physical_total_bytes=$m.total;physical_available_bytes=$m.available;commit_limit_bytes=$m.pageTotal;commit_available_bytes=$m.pageAvailable;commit_used_bytes=($m.pageTotal-$m.pageAvailable);source='GlobalMemoryStatusEx';scope='CURRENT_WINDOWS_HOST';solver_calls=0}
}
function Write-Atomic($data) {
 $full=[IO.Path]::GetFullPath($OutputPath); [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($full)) | Out-Null
 $temp=$full+'.tmp'; [IO.File]::WriteAllText($temp,($data|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temp -Destination $full -Force
}
if($WatchSeconds -gt 0){
 # One lightweight persistent Windows process; no repeated CIM queries.
 while($true){ Write-Atomic (Sample); Start-Sleep -Seconds $WatchSeconds }
}
$data=Sample
$data.user_profile=[Environment]::GetFolderPath('UserProfile')
$cfg=Join-Path $data.user_profile '.wslconfig';$data.wslconfig_path=$cfg;$data.wslconfig_exists=Test-Path -LiteralPath $cfg
$data.wslconfig_resource_settings=@()
if($data.wslconfig_exists){
 $data.wslconfig_sha256=(Get-FileHash -LiteralPath $cfg -Algorithm SHA256).Hash.ToLowerInvariant()
 $data.wslconfig_resource_settings=@(Get-Content -LiteralPath $cfg | Where-Object {$_ -match '^\s*(\[wsl2\]|memory\s*=|swap\s*=|swapFile\s*=|processors\s*=|autoMemoryReclaim\s*=)'})
}
$data.processes=@(Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 20 ProcessName,Id,WorkingSet64,PrivateMemorySize64)
$data.vmmem_working_set_bytes=(@(Get-Process -Name 'vmmem*' -ErrorAction SilentlyContinue)|Measure-Object -Property WorkingSet64 -Sum).Sum
try{$data.pagefile=@(Get-CimInstance Win32_PageFileUsage | Select-Object Name,AllocatedBaseSize,CurrentUsage,PeakUsage);$data.pagefile_settings=@(Get-CimInstance Win32_PageFileSetting | Select-Object Name,InitialSize,MaximumSize);$data.automatic_pagefile=(Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile;$data.installed_module_capacity_bytes=(Get-CimInstance Win32_PhysicalMemory|Measure-Object -Property Capacity -Sum).Sum}catch{$data.cim_error=$_.Exception.Message}
function WslText([string]$argsText){
 $info=[Diagnostics.ProcessStartInfo]::new('wsl.exe',$argsText);$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.StandardOutputEncoding=[Text.Encoding]::Unicode
 $p=[Diagnostics.Process]::Start($info);$text=$p.StandardOutput.ReadToEnd();$p.WaitForExit();if($p.ExitCode -ne 0){throw 'Read-only WSL inventory failed'};return $text.Trim()
}
$data.wsl_version=WslText '--version'
$data.wsl_distributions=WslText '--list --verbose'
$data.container_related_processes=@(Get-Process | Where-Object {$_.ProcessName -match 'docker|podman|containerd|vmmem'} | Select-Object ProcessName,Id,WorkingSet64)
$data.host_disks=@(Get-PSDrive -PSProvider FileSystem|Select-Object Name,Used,Free)
Write-Atomic $data
$data|ConvertTo-Json -Depth 8
