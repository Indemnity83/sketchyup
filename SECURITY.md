# Security policy

## Supported versions

Security fixes go into the latest release. Check the [releases page](https://github.com/zygote55/sketchyup/releases/latest) for the current version, and upgrade before reporting if you can.

## Reporting a vulnerability

Please report privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**, or go straight to [a new advisory](https://github.com/zygote55/sketchyup/security/advisories/new). Do not open a public issue for a security problem.

Include the SketchyUp version (`sketchyup --version`), how to reproduce the problem, and a sample file if one is needed. Build the sample yourself, and do not send models that contain anyone's private data.

SketchyUp has one maintainer, so reports are handled as time allows. A fixed problem is named in the [release notes](docs/RELEASE_NOTES.md) of the release that fixes it, with credit if you want it.

## What is in scope

SketchyUp reads files that may come from anywhere, so these areas matter most:

- **File readers:** native `.sketchyup` files and the importers for `.skp`, IFC, STEP, GLB/glTF, OBJ/MTL, STL, DXF, GeoTIFF and images.
- **The helper sandbox:** the `.skp`, IFC, STEP, text, extension and Blender helpers run under Landlock and seccomp ([ADR 0183](docs/decisions/0183-helper-process-sandbox.md)). A way for a helper to escape its policy is in scope.
- **Local automation:** the MCP server (`sketchyup-cli --mcp`), the native inspection socket and headless sessions.
- **The assistant:** the handling of provider credentials (kept in the Secret Service, never in files) and of the model context sent to a provider.
