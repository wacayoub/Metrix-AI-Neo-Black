"""Build a deterministic, self-contained GitHub handoff, without publication."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    dist = ROOT / "dist"
    manifest = json.loads((dist / "manifest.json").read_text(encoding="utf-8"))
    build = json.loads((dist / "BUILD_REPORT.json").read_text(encoding="utf-8"))
    github = json.loads((dist / "GITHUB_PREPARATION.json").read_text(encoding="utf-8"))
    if build["result"] != "PASS" or github["result"] != "PASS" or github["published"]:
        raise ValueError("Delivery requires validated, unpublished inputs")
    files = {}
    for item in manifest["packages"] + [manifest["source"]]:
        path = dist / item["file"]
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != item["sha256"] or digest != build["artifacts"][path.name]:
            raise ValueError("Artifact checksum mismatch: " + path.name)
        files[("sources/" if path.suffix == ".zip" else "packages/") + path.name] = content
    patch = dist / github["patch"]
    if hashlib.sha256(patch.read_bytes()).hexdigest() != github["sha256"]:
        raise ValueError("GitHub patch checksum mismatch")
    files["github/" + patch.name] = patch.read_bytes()
    for name in ("manifest.json", "BUILD_REPORT.json", "GITHUB_PREPARATION.json", "SHA256SUMS"):
        files["build/" + name] = (dist / name).read_bytes()
    for directory in ("docs", "reports", "LICENSES"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file():
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    files["README_LIVRAISON.md"] = (
        "# Livraison Metrix NEO / Advanced 0.1.0\n\n"
        "Menus des deux thèmes validés visuellement le 25 octobre 2026.\n"
        "Aucun accès ni installation sur le Vu+. GitHub préparé, non publié.\n\n"
        "- packages/ : les deux skins et le runtime nécessaire ; helper facultatif.\n"
        "- sources/ : code, tests, ressources et aperçus dans le ZIP source.\n"
        "- github/ : patch binaire additif pour wacayoub/Metrix-AI-Neo-Black.\n"
        "- docs/GITHUB_PREPARATION.md : procédure et base auditées.\n"
        "- docs/GITHUB_PR_BODY.md : description de PR préparée.\n"
        "- docs/RELEASE_NOTES_0.1.0.md : notes de version préparées.\n"
        "- docs/DELIVERY_REPORT.md et reports/ : résultats et limites.\n"
        "- build/ : manifestes et empreintes des artefacts.\n\n"
        "Le runtime commun est obligatoire pour chaque skin ; le helper Smart est optionnel.\n"
        "Compatibilité du build personnel OpenATV 8.0.1 non vérifiée sur matériel.\n"
        "Les manifestes de préparation ne donnent aucune autorisation d’installation.\n\n"
        "SHA256SUMS vérifie chaque fichier de cette livraison après extraction.\n"
    ).encode("utf-8")
    sums = "".join(hashlib.sha256(data).hexdigest() + "  " + name + "\n" for name, data in sorted(files.items()))
    files["SHA256SUMS"] = sums.encode("utf-8")
    output = dist / "metrix-neo-0.1.0-github-delivery.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo("metrix-neo-delivery/" + name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data)
    with zipfile.ZipFile(output) as bundle:
        if bundle.testzip() is not None or len(bundle.namelist()) != len(files):
            raise ValueError("Invalid delivery ZIP")
        for name, data in files.items():
            if bundle.read("metrix-neo-delivery/" + name) != data:
                raise ValueError("Delivery round-trip mismatch: " + name)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (dist / "DELIVERY_SHA256SUMS").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    print(json.dumps({"result": "PASS", "file": output.name, "bytes": output.stat().st_size, "sha256": digest, "entries": len(files), "published": False, "receiver_access": False}, indent=2))


if __name__ == "__main__":
    main()
