import json
import re
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    req_file = root / "requirements.txt"
    manifest_file = root / "custom_components" / "open_meteo_custom" / "manifest.json"

    if not req_file.exists():
        print("requirements.txt not found")
        return

    if not manifest_file.exists():
        print("manifest.json not found")
        return

    # Parse requirements.txt for openmeteo-sdk version
    open_meteo_ver = None
    with open(req_file, "r") as f:
        for line in f:
            match = re.match(r"^openmeteo-sdk\s*==\s*([0-9a-zA-Z\.\-]+)", line.strip())
            if match:
                open_meteo_ver = match.group(1)
                break

    if not open_meteo_ver:
        print("openmeteo-sdk version not found in requirements.txt")
        return

    # Load and update manifest.json
    with open(manifest_file, "r") as f:
        manifest = json.load(f)

    # Find the openmeteo-sdk requirement in requirements list
    requirements = manifest.get("requirements", [])
    updated = False
    for idx, req in enumerate(requirements):
        if req.startswith("openmeteo-sdk=="):
            new_req = f"openmeteo-sdk=={open_meteo_ver}"
            if req != new_req:
                requirements[idx] = new_req
                updated = True
                print(f"Updated manifest requirement to {new_req}")
            break

    if updated:
        manifest["requirements"] = requirements
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")  # Ensure trailing newline
        print("manifest.json successfully updated")
    else:
        print("manifest.json requirement is already up to date")

if __name__ == "__main__":
    main()
