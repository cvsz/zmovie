# Model storage policy

Keep the model weights required by the current production renderer on local Linux storage for predictable access during long CPU renders. Less frequently used model bundles may be archived to Windows SMB, but should be staged back to local storage and verified before a production run. The SMB closeout wrapper does not move models automatically.
