# SMB integration with the five closeout gates

SMB preflight runs before Gate 1 so the closeout cannot begin under a false storage assumption. Gates 1–5 remain unchanged and authoritative: latest-main deployment, restart/recovery, renderer/hardware policy, real-model evidence, and N2N production acceptance. After Gate 5, the wrapper archives the evidence set to Windows SMB and SHA-256 verifies it. SMB therefore extends the evidence/data layer without changing the meaning of the five production gates.
