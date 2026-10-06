[CmdletBinding()]
param([Parameter(Mandatory)][string]$EvidenceDirectory)
$ErrorActionPreference='Stop'
$probe=Join-Path $PSScriptRoot 'Get-Gate5HostResources.ps1'
. $probe -LibraryOnly
if(Test-Path -LiteralPath $EvidenceDirectory){throw 'Use a new test evidence directory'}
New-Item -ItemType Directory -Path $EvidenceDirectory|Out-Null
$checks=New-Object 'System.Collections.Generic.List[object]'
function Assert($Condition,[string]$Message){if(!$Condition){throw $Message}}
function Passed([string]$Name){$checks.Add([ordered]@{test=$Name;status='PASS'});Write-Host $Name PASS}
function Expect-Failure([scriptblock]$Action,[string]$Name){$failed=$false;try{& $Action|Out-Null}catch{$failed=$true};Assert $failed $Name}
function Check-Primitive($Value){
 if($null -eq $Value){return}
 if($Value -is [string]){Assert (@($Value.PSObject.Properties|Where-Object{$_.Name -ne 'Length'}).Count -eq 0) 'String has ETS metadata';return}
 if($Value -is [long] -or $Value -is [bool]){return}
 if($Value -is [Collections.IDictionary]){foreach($k in $Value.Keys){Assert ($k -is [string]) 'Key is not string';Check-Primitive $Value[$k]};return}
 if($Value -is [Array]){foreach($item in $Value){Check-Primitive $item};return}
 throw ('Non-primitive type '+$Value.GetType().FullName)
}
$memory=[ordered]@{observed_at='2026-10-07T00:00:00.0000000Z';physical_total_bytes=[long]17179869184;physical_available_bytes=[long]12884901888;commit_limit_bytes=[long]34359738368;commit_available_bytes=[long]21474836480;commit_used_bytes=[long]12884901888;source='GlobalMemoryStatusEx';scope='CURRENT_WINDOWS_HOST';solver_calls=[long]0}
$missing=Join-Path $EvidenceDirectory 'absent.wslconfig'
$empty=New-Gate5HostRecord -Memory $memory -UserProfile $EvidenceDirectory -ConfigPath $missing -WslVersion '' -WslDistributions ''
Check-Primitive $empty
Assert (!$empty.wslconfig_exists -and $empty.wslconfig_resource_settings -is [Array] -and $empty.wslconfig_resource_settings.Count -eq 0) 'Absent config mismatch'
Passed 'wslconfig_absent_plain_empty_settings'
$emptyJson=Write-Gate5AtomicJson $empty (Join-Path $EvidenceDirectory 'empty.json')
$read=$emptyJson|ConvertFrom-Json
foreach($name in @('processes','pagefile','pagefile_settings','container_related_processes','host_disks')){Assert ($read.$name -is [Array] -and $read.$name.Count -eq 0) ('Empty array lost: '+$name)}
Assert ($null -eq $read.automatic_pagefile -and $null -eq $read.vmmem_working_set_bytes) 'Null optional values lost'
Passed 'empty_process_pagefile_disk_arrays_and_nulls'
$cfg=Join-Path $EvidenceDirectory 'candidate.wslconfig'
[IO.File]::WriteAllText($cfg,"[wsl2]`nmemory=11GB`nswap=4GB`nswapFile=D:\\WSLDistros\\wsl-swap\\swap.vhdx`n",[Text.UTF8Encoding]::new($false))
$unicode='WSL '+[char]0x7248+[char]0x672C+": 2.7.14`r`nUbuntu "+[char]0x4E2D+[char]0x6587+"`nline3"
$processes=@([pscustomobject]@{ProcessName=$unicode;Id=17;WorkingSet64=[long]4294967301;PrivateMemorySize64=[long]5000000000;Extra=[Diagnostics.Process]::GetCurrentProcess()},[pscustomobject]@{ProcessName='vmmemWSL';Id=18;WorkingSet64=[long]3000000000;PrivateMemorySize64=[long]4000000000})
$pages=@([pscustomobject]@{Name='C:\pagefile.sys';AllocatedBaseSize=9728;CurrentUsage=123;PeakUsage=456},[pscustomobject]@{Name='D:\fixture-only-pagefile.sys';AllocatedBaseSize=2048;CurrentUsage=0;PeakUsage=1})
$settings=@([pscustomobject]@{Name='C:\pagefile.sys';InitialSize=0;MaximumSize=0},[pscustomobject]@{Name='D:\fixture-only-pagefile.sys';InitialSize=2048;MaximumSize=4096})
$disks=@([pscustomobject]@{Name='C';Used=[long]100000000000;Free=[long]90000000000;Extra=[IO.DirectoryInfo]::new($EvidenceDirectory)},[pscustomobject]@{Name='D';Used=[long]300000000000;Free=[long]380000000000})
$full=New-Gate5HostRecord -Memory $memory -UserProfile $EvidenceDirectory -ConfigPath $cfg -Processes $processes -VmmemProcesses @($processes[1]) -Pagefiles $pages -PagefileSettings $settings -AutomaticPagefile $true -InstalledCapacity ([long]17179869184) -WslVersion $unicode -WslDistributions $unicode -ContainerProcesses @($processes[1]) -Disks $disks
Check-Primitive $full
Assert ($full.wslconfig_exists -and $full.wslconfig_resource_settings.Count -eq 4 -and $full.wslconfig_sha256 -eq (Get-FileHash -LiteralPath $cfg -Algorithm SHA256).Hash.ToLowerInvariant()) 'Candidate config mismatch'
Passed '11GB_4GB_D_swap_config_and_hash'
Assert ($full.processes.Count -eq 2 -and $full.pagefile.Count -eq 2 -and $full.pagefile_settings.Count -eq 2 -and $full.host_disks.Count -eq 2) 'Multiple records lost'
Assert ($full.processes[0].WorkingSet64 -eq 4294967301 -and $full.pagefile[0].AllocatedBaseSize -eq 9728 -and $full.vmmem_working_set_bytes -eq 3000000000) 'Bytes/MiB changed'
Passed 'multiple_process_CIM_disk_explicit_records_original_units'
$path=Join-Path $EvidenceDirectory 'full.json'
$json=Write-Gate5AtomicJson $full $path
$read=[IO.File]::ReadAllText($path,[Text.Encoding]::UTF8)|ConvertFrom-Json
Assert ($read.wsl_version -ceq $unicode -and $read.wsl_distributions -ceq $unicode -and $read.processes[0].ProcessName -ceq $unicode) 'Unicode/newlines changed'
Assert ($json -notmatch '"(PSDrive|PSProvider|Extra)"') 'Rich object metadata leaked'
Passed 'Unicode_multiline_JSON_disk_roundtrip_no_rich_properties'
Assert ($read.physical_total_bytes -eq 17179869184 -and $read.processes[0].WorkingSet64 -eq 4294967301) 'int64 readback changed'
Passed 'all_schema_values_primitives_and_int64_preserved'
# Regression: the exact Get-Content shape that grows the legacy serializer graph.
$decorated=@(Get-Content -LiteralPath $cfg)
Assert (@($decorated[0].PSObject.Properties|Where-Object{$_.Name -eq 'PSDrive'}).Count -eq 1) 'Regression fixture lacks Get-Content metadata'
$safe=ConvertTo-Gate5PlainValue ([ordered]@{wslconfig_resource_settings=$decorated})
Check-Primitive $safe
$safeJson=Write-Gate5AtomicJson $safe (Join-Path $EvidenceDirectory 'decorated_string_regression.json')
Assert ($safeJson.Length -lt 1024 -and (($safeJson|ConvertFrom-Json).wslconfig_resource_settings[1] -eq 'memory=11GB')) 'Metadata regression'
Passed 'Get_Content_string_ETS_metadata_stripped_before_serializer'
$original=[IO.File]::ReadAllText($path)
$full.observed_at='2026-10-07T00:00:01.0000000Z'
$replacement=Write-Gate5AtomicJson $full $path
Assert ([IO.File]::ReadAllText($path+'.previous') -ceq $original) 'Atomic previous record missing'
Assert ([IO.File]::ReadAllText($path) -ceq $replacement) 'Atomic replacement failed'
Passed 'atomic_initial_publish_replace_and_previous_record'
$negative=Join-Path $EvidenceDirectory 'must_not_exist.json'
Expect-Failure {Write-Gate5AtomicJson ([ordered]@{bad=[pscustomobject]@{Name='rich'}}) $negative} 'Rich object accepted'
Assert (!(Test-Path -LiteralPath $negative)) 'Failed serialization published a file'
Passed 'rich_object_rejected_no_final_or_half_JSON'
Expect-Failure {Write-Gate5AtomicJson ([ordered]@{bad=1.5}) $negative} 'Double accepted'
Expect-Failure {Write-Gate5AtomicJson ([ordered]@{bad=[uint64]::MaxValue}) $negative} 'Overflow accepted'
Expect-Failure {Write-Gate5AtomicJson ([ordered]@{bad=[datetime]::Now}) $negative} 'DateTime object accepted'
Passed 'non_schema_float_DateTime_and_int64_overflow_rejected'
$cycle=[ordered]@{};$cycle.self=$cycle
Expect-Failure {Write-Gate5AtomicJson $cycle $negative} 'Recursive dictionary accepted'
Passed 'recursive_graph_fails_bounded_before_serialization'
$before=[IO.File]::ReadAllText($path)
Expect-Failure {Write-Gate5AtomicJson ([ordered]@{bad=[Diagnostics.Process]::GetCurrentProcess()}) $path} 'Process accepted'
Assert ([IO.File]::ReadAllText($path) -ceq $before) 'Failed serialization changed prior valid record'
Passed 'failed_serialization_preserves_previous_valid_record'
$locked=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try {Expect-Failure {Write-Gate5AtomicJson ([ordered]@{new='must-not-publish'}) $path} 'Replace of locked target unexpectedly succeeded'}finally{$locked.Dispose()}
Assert ([IO.File]::ReadAllText($path) -ceq $before) 'Failed replace changed old file'
Assert (@(Get-ChildItem -LiteralPath $EvidenceDirectory -Filter '*.tmp').Count -eq 0) 'Temporary JSON left after failure'
Passed 'failed_atomic_replace_cleans_temp_preserves_valid_final'
$cimFailure=New-Gate5HostRecord -Memory $memory -UserProfile $EvidenceDirectory -ConfigPath $missing -CimError 'CIM unavailable' -WslVersion '' -WslDistributions ''
Assert ($cimFailure.cim_error -eq 'CIM unavailable' -and $null -eq $cimFailure.automatic_pagefile) 'CIM diagnostics lost'
Check-Primitive $cimFailure
Passed 'CIM_failure_diagnostic_preserved_without_invented_values'
$live=Get-Gate5MemorySample;Check-Primitive $live
Assert ($live.physical_available_bytes -gt 0 -and $live.commit_available_bytes -gt 0) 'Live memory sampler failed'
Passed 'native_live_sample_and_watch_schema_remain_int64_bytes'
$receipt=[ordered]@{status='PASS';powershell=[string]$PSVersionTable.PSVersion.ToString();edition=[string]$PSVersionTable.PSEdition;probe_sha256=[string](Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash.ToLowerInvariant();test_sha256=[string](Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();checks=$checks.ToArray();solver_runs=[long]0;settings_changed=$false}
Write-Gate5AtomicJson $receipt (Join-Path $EvidenceDirectory 'PROBE_TESTS.json')
