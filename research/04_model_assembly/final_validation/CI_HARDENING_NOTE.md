# Repository housekeeping

Independent commits92a48648 anddea5e242 adds bounded OSM retries (3 attempts;2/4second backoff;15sconnect/120sread timeout), atomic nonempty response writes, content-length checks and SHA256receipt cache verification. Existing earth-osm companionMD5 checks remain in place for PBF. GitHub OS jobs cache the PBF/checksum/receipt directory with a dependency/helper-specific key. Exhausted requests raise EXTERNAL_OSM_SERVICE_FAILURE; no empty download substitute, skipped OSM test or research input change is introduced.

Three deterministic local download tests passed: transient retry plus cache reuse, empty/truncated response rejection, corrupt-cache plus bounded-outage rejection. The18 assembly-input regressions passed, including approved null/nonposting bunker coverage and historical PENDING tested against a frozen fixture. Live GitHub OS CI and remote download availability were not rerun; their status is NOT_VERIFIED_THIS_PACKAGE. Existing legitimate zero-feature output behavior was not repurposed as a failed-download fallback.

CodeQL infrastructure/upload status was not reclassified as a Python analysis result and its workflow was not changed. No fresh CodeQL run is claimed. These external CI matters did not prevent the actual Gate5 solve.
