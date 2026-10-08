# Security Policy

## Supported Versions

Security maintenance currently covers the latest patch release in the Azimlib
0.3 series. Reports affecting that series are accepted for triage; users should
upgrade to the latest available patch. Older versions do not receive maintained
security fixes.

| Version | Supported |
| --- | --- |
| 0.3.x | ✅ |
| 0.2.x | ❌ |
| < 0.2.0 | ❌ |

These are **Azimlib versions**, not Python versions. The published package
requires Python 3.10 or newer; release CI covers CPython 3.10–3.14 on Windows,
Linux and macOS. Interpreter compatibility is separate from this security policy.

## Reporting a Vulnerability

Use **Security → Report a vulnerability** on
[the GitHub repository](https://github.com/Kernerian/azimlib/security).
Private vulnerability reporting is enabled. Do not disclose exploitable details,
tokens or private datasets in public issues or pull requests.

Include the affected Azimlib/Python versions, operating system, a minimal
reproduction and the expected impact. Geographic parsers, archives, HTML/SVG
output and denial-of-service concerns are relevant security reports.

If the private reporting channel is unavailable, contact a maintainer through
their published GitHub profile to arrange a private channel before sharing
details. Azimlib does not use a third-party security coordinator. No response
deadline, guaranteed fix or bug bounty is promised.

Ordinary rendering defects can be reported through GitHub Issues without
sensitive material. Coordinate any public vulnerability disclosure privately.
