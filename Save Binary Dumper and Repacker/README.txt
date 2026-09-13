Unpacker auto detects plist in the same dir and tries to unpack all the plists. In practice, just put the one plist you want to unpack in the same dir as the unpacker.
Repacker auto detects for the 3 binary files in the same dir, and repacks it into a single plist. Equivalent to PoC v2 version.

For both, manual file management of the plists and the binary files will have to be done.
Main use case of the unpacker and repacker is to inspect and/or edit the profile beyond what the save editor offers