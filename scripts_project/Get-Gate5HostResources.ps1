[CmdletBinding()]
param([string]$OutputPath='', [int]$WatchSeconds=0, [switch]$LibraryOnly)
$ErrorActionPreference='Stop'

function ConvertTo-Gate5PlainValue {
 param([AllowNull()][object]$Value, [string]$Path='$', [int]$Level=0)
 if($Level -gt 8){throw "JSON schema exceeds depth at $Path"}
 if($null -eq $Value){return $null}
 if($Value -is [string]){return [string]::Copy($Value)} # Also strip ETS metadata on strings.
 if($Value -is [bool]){return [bool]$Value}
 if($Value -is [byte] -or $Value -is [sbyte] -or $Value -is [int16] -or $Value -is [uint16] -or $Value -is [int32] -or $Value -is [uint32] -or $Value -is [int64] -or $Value -is [uint64]){return [long]$Value}
 if($Value -is [Collections.IDictionary]){
  $record=[ordered]@{}
  foreach($key in $Value.Keys){
   if($key -isnot [string]){throw "Non-string dictionary key at $Path"}
   $record[[string]::Copy($key)]=ConvertTo-Gate5PlainValue -Value $Value[$key] -Path ($Path+'.'+$key) -Level ($Level+1)
  }
  return $record
 }
 if($Value -is [Array] -and $Value.Rank -eq 1){
  $items=New-Object 'System.Collections.Generic.List[object]'
  for($i=0;$i -lt $Value.Length;$i++){$items.Add((ConvertTo-Gate5PlainValue -Value $Value[$i] -Path ($Path+'['+$i+']') -Level ($Level+1)))}
  return ,$items.ToArray()
 }
 throw "Non-primitive JSON value at ${Path}: $($Value.GetType().FullName)"
}

function Write-Gate5AtomicJson {
 param([Parameter(Mandatory)][Collections.IDictionary]$Data,[Parameter(Mandatory)][string]$Path)
 # Validate/normalize the entire graph BEFORE creating a temporary file.
 $plain=ConvertTo-Gate5PlainValue -Value $Data
 $json=ConvertTo-Json -InputObject $plain -Depth 8
 $null=ConvertFrom-Json -InputObject $json -ErrorAction Stop
 $full=[IO.Path]::GetFullPath($Path)
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($full))|Out-Null
 $temp=$full+'.'+[Guid]::NewGuid().ToString('N')+'.tmp'
 try {
  [IO.File]::WriteAllText($temp,$json,[Text.UTF8Encoding]::new($false))
  $disk=[IO.File]::ReadAllText($temp,[Text.Encoding]::UTF8)
  if($disk -cne $json){throw 'JSON disk readback mismatch'}
  $null=ConvertFrom-Json -InputObject $disk -ErrorAction Stop
  if([IO.File]::Exists($full)){
   # Atomic replacement on NTFS; retain the prior complete record for audit.
   [IO.File]::Replace($temp,$full,$full+'.previous')
  }else{[IO.File]::Move($temp,$full)}
 } finally {
  if([IO.File]::Exists($temp)){[IO.File]::Delete($temp)}
 }
 return $json
}

function Get-Gate5MemorySample {
 if(-not ('Gate5Memory' -as [type])){
  Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Gate5Memory {
 [StructLayout(LayoutKind.Sequential)] public struct M { public uint length,load; public ulong total,available,pageTotal,pageAvailable,virtualTotal,virtualAvailable,extended; }
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool GlobalMemoryStatusEx(ref M value);
 public static M Read(){ M x=new M(); x.length=(uint)Marshal.SizeOf(typeof(M)); if(!GlobalMemoryStatusEx(ref x)) throw new Exception("GlobalMemoryStatusEx failed"); return x; }
}
'@
 }
 $m=[Gate5Memory]::Read()
 return [ordered]@{observed_at=[DateTime]::UtcNow.ToString('o');physical_total_bytes=[long]$m.total;physical_available_bytes=[long]$m.available;commit_limit_bytes=[long]$m.pageTotal;commit_available_bytes=[long]$m.pageAvailable;commit_used_bytes=[long]($m.pageTotal-$m.pageAvailable);source='GlobalMemoryStatusEx';scope='CURRENT_WINDOWS_HOST';solver_calls=[long]0}
}

function ConvertTo-Gate5ProcessRecords {
 param([object[]]$Items=@(),[switch]$Container)
 $records=New-Object 'System.Collections.Generic.List[object]'
 foreach($item in $Items){
  $record=[ordered]@{ProcessName=[string]::Copy([string]$item.ProcessName);Id=[long]$item.Id;WorkingSet64=[long]$item.WorkingSet64}
  if(!$Container){$record.PrivateMemorySize64=[long]$item.PrivateMemorySize64}
  $records.Add($record)
 }
 return ,$records.ToArray()
}

function New-Gate5HostRecord {
 param([Collections.IDictionary]$Memory,[string]$UserProfile,[string]$ConfigPath,
       [object[]]$Processes=@(),[object[]]$VmmemProcesses=@(),[object[]]$Pagefiles=@(),[object[]]$PagefileSettings=@(),
       [AllowNull()][object]$AutomaticPagefile=$null,[AllowNull()][object]$InstalledCapacity=$null,[AllowNull()][string]$CimError,
       [string]$WslVersion,[string]$WslDistributions,[object[]]$ContainerProcesses=@(),[object[]]$Disks=@())
 $data=ConvertTo-Gate5PlainValue -Value $Memory
 $data.user_profile=[string]::Copy($UserProfile);$data.wslconfig_path=[string]::Copy($ConfigPath)
 $data.wslconfig_exists=[bool][IO.File]::Exists($ConfigPath)
 $data.wslconfig_resource_settings=@()
 if($data.wslconfig_exists){
  $data.wslconfig_sha256=[string]::Copy((Get-FileHash -LiteralPath $ConfigPath -Algorithm SHA256).Hash.ToLowerInvariant())
  # File.ReadAllLines returns plain System.String, unlike Get-Content's ETS-wrapped lines.
  $data.wslconfig_resource_settings=@([IO.File]::ReadAllLines($ConfigPath)|Where-Object{$_ -match '^\s*(\[wsl2\]|memory\s*=|swap\s*=|swapFile\s*=|processors\s*=|autoMemoryReclaim\s*=)'}|ForEach-Object{[string]::Copy($_)})
 }
 $data.processes=ConvertTo-Gate5ProcessRecords -Items $Processes
 $data.vmmem_working_set_bytes=$null
 if($VmmemProcesses.Count -gt 0){[long]$sum=0;foreach($p in $VmmemProcesses){$sum+=[long]$p.WorkingSet64};$data.vmmem_working_set_bytes=$sum}
 $data.pagefile=@(foreach($p in $Pagefiles){[ordered]@{Name=[string]::Copy([string]$p.Name);AllocatedBaseSize=[long]$p.AllocatedBaseSize;CurrentUsage=[long]$p.CurrentUsage;PeakUsage=[long]$p.PeakUsage}})
 $data.pagefile_settings=@(foreach($p in $PagefileSettings){[ordered]@{Name=[string]::Copy([string]$p.Name);InitialSize=[long]$p.InitialSize;MaximumSize=[long]$p.MaximumSize}})
 $data.automatic_pagefile=if($null -eq $AutomaticPagefile){$null}else{[bool]$AutomaticPagefile}
 $data.installed_module_capacity_bytes=if($null -eq $InstalledCapacity){$null}else{[long]$InstalledCapacity}
 if($CimError){$data.cim_error=[string]::Copy($CimError)}
 $data.wsl_version=[string]::Copy($WslVersion);$data.wsl_distributions=[string]::Copy($WslDistributions)
 $data.container_related_processes=ConvertTo-Gate5ProcessRecords -Items $ContainerProcesses -Container
 $data.host_disks=@(foreach($p in $Disks){[ordered]@{Name=[string]::Copy([string]$p.Name);Used=if($null -eq $p.Used){$null}else{[long]$p.Used};Free=if($null -eq $p.Free){$null}else{[long]$p.Free}}})
 return (ConvertTo-Gate5PlainValue -Value $data)
}

function Get-Gate5WslText {
 param([string]$Arguments)
 $info=[Diagnostics.ProcessStartInfo]::new('wsl.exe',$Arguments)
 $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.StandardOutputEncoding=[Text.Encoding]::Unicode
 $p=[Diagnostics.Process]::Start($info)
 try {$text=$p.StandardOutput.ReadToEnd();$p.WaitForExit();if($p.ExitCode -ne 0){throw 'Read-only WSL inventory failed'};return [string]::Copy($text.Trim())}
 finally {$p.Dispose()}
}

if($LibraryOnly){return}
if(!$OutputPath){throw 'OutputPath is required'}
if($WatchSeconds -lt 0){throw 'WatchSeconds must not be negative'}
if($WatchSeconds -gt 0){while($true){$null=Write-Gate5AtomicJson -Data (Get-Gate5MemorySample) -Path $OutputPath;Start-Sleep -Seconds $WatchSeconds}}

# Retain all previous read-only collection fields and units. No command lines collected.
$userProfile=[Environment]::GetFolderPath('UserProfile')
$processes=@(Get-Process|Sort-Object WorkingSet64 -Descending|Select-Object -First 20)
$vmmem=@(Get-Process -Name 'vmmem*' -ErrorAction SilentlyContinue)
$pagefiles=@();$settings=@();$automatic=$null;$capacity=$null;$cimError=$null
try {
 $pagefiles=@(Get-CimInstance Win32_PageFileUsage);$settings=@(Get-CimInstance Win32_PageFileSetting)
 $automatic=(Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile
 [long]$capacity=0;foreach($module in @(Get-CimInstance Win32_PhysicalMemory)){$capacity+=[long]$module.Capacity}
}catch{$cimError=[string]$_.Exception.Message}
$version=Get-Gate5WslText '--version';$distributions=Get-Gate5WslText '--list --verbose'
$containers=@(Get-Process|Where-Object{$_.ProcessName -match 'docker|podman|containerd|vmmem'})
$disks=@(Get-PSDrive -PSProvider FileSystem)
$data=New-Gate5HostRecord -Memory (Get-Gate5MemorySample) -UserProfile $userProfile -ConfigPath (Join-Path $userProfile '.wslconfig') -Processes $processes -VmmemProcesses $vmmem -Pagefiles $pagefiles -PagefileSettings $settings -AutomaticPagefile $automatic -InstalledCapacity $capacity -CimError $cimError -WslVersion $version -WslDistributions $distributions -ContainerProcesses $containers -Disks $disks
Write-Gate5AtomicJson -Data $data -Path $OutputPath
