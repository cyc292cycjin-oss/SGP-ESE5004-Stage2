[CmdletBinding()]
param(
 [string]$EvidenceDirectory = 'D:\ResearchWorkspaces\ASEAN\work\gate5_host_monitor',
 [switch]$ShowPaths
)
$ErrorActionPreference='Stop'
$workspaceRoot=Split-Path -Parent $PSScriptRoot
if($workspaceRoot -ne 'D:\ResearchWorkspaces\ASEAN'){throw 'Unexpected workspace root'}
$evidence=[IO.Path]::GetFullPath($EvidenceDirectory)
if(!$evidence.StartsWith($workspaceRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'EvidenceDirectory must remain inside D workspace'}
$probe=Join-Path $PSScriptRoot 'Get-Gate5HostResources.ps1'
if($ShowPaths){[ordered]@{Workspace=$workspaceRoot;EvidenceDirectory=$evidence;Probe=$probe;Mode='PREFLIGHT_ONLY';ExecuteAllowed=$false}|ConvertTo-Json;return}
# Use the repaired live probe; preserve historical delivery scripts byte-for-byte.
# No Execute parameter or authorization forwarding.
New-Item -ItemType Directory -Force -Path $evidence|Out-Null
$hostFile=Join-Path $evidence 'HOST_RESOURCE_SNAPSHOT.json'
$resultFile=Join-Path $evidence 'RESOURCE_PREFLIGHT.json'
& $probe -OutputPath $hostFile|Out-Null
$hostLinux='/mnt/d/'+$hostFile.Substring(3).Replace('\','/')
$resultLinux='/mnt/d/'+$resultFile.Substring(3).Replace('\','/')
& wsl.exe -d Ubuntu --cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model -- /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts_project/gate5_memory_preflight.py --host-report $hostLinux --output $resultLinux
exit $LASTEXITCODE
