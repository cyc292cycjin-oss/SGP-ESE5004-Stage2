param([switch]$Execute,[string]$AuthorizationFile='', [string]$EvidenceDirectory=(Join-Path $env:USERPROFILE 'Documents\ChatGPT\ASEAN\work\gate5_host_monitor'))
$ErrorActionPreference='Stop'
$taskHostMonitorJob=$null
# Default is preflight ONLY. Never edits .wslconfig or stops WSL.
$repo='/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model'
$python='/home/jin/miniforge3/envs/pypsa-earth/bin/python'
New-Item -ItemType Directory -Force -Path $EvidenceDirectory|Out-Null
$hostFile=Join-Path $EvidenceDirectory 'HOST_RESOURCE_SNAPSHOT.json'
$resultFile=Join-Path $EvidenceDirectory 'RESOURCE_PREFLIGHT.json'
$probe=Join-Path $PSScriptRoot 'Get-Gate5HostResources.ps1'
& $probe -OutputPath $hostFile | Out-Null
function LinuxPath([string]$path) {
 $normalized=[IO.Path]::GetFullPath($path).Replace('\','/')
 $converted=& wsl.exe -d Ubuntu -e wslpath -u $normalized
 if($LASTEXITCODE -ne 0 -or !$converted){throw 'WSL path conversion failed'}
 return ($converted|Out-String).Trim()
}
$hostLinux=LinuxPath $hostFile
$resultLinux=LinuxPath $resultFile
$callArgs=@('-d','Ubuntu','--cd',$repo,'--',$python,'scripts_project/gate5_memory_preflight.py','--host-report',$hostLinux,'--output',$resultLinux)
if($Execute){
 if(!$AuthorizationFile){throw 'No later human resource/run authorization supplied. Nothing launched.'}
 $authLinux=LinuxPath $AuthorizationFile
 $callArgs+=@('--execute','--authorization',$authLinux)
 # One persistent lightweight host sampler; never inspect solver APIs.
 $taskHostMonitorJob=Start-Job -FilePath $probe -ArgumentList @($hostFile,10)
}
try { & wsl.exe @callArgs; $resultCode=$LASTEXITCODE }
finally {if($taskHostMonitorJob){Stop-Job $taskHostMonitorJob;Remove-Job $taskHostMonitorJob}}
exit $resultCode
