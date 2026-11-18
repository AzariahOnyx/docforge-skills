"""Load a pack folder, check it, hash it, and copy what a run uses into the run.

Safety: every path named in pack.yaml must stay inside the pack folder after
symlinks are resolved, must exist, and is size-capped. The pack's hash covers
pack.yaml and every file it names, so any change gives a new hash.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import shutil

from pydantic import ValidationError
import yaml

from docforge.config import DocForgeConfig

from .model import STAGES, PackManifest, applies

MANIFEST = "pack.yaml"
MAX_FILE_BYTES = 1024 * 1024
MAX_PACK_BYTES = 20 * 1024 * 1024
MAX_FILES = 500
RUN_FOLDER = "pack"
RULE = ("Pack material governs format, structure and style. It never overrides the run's sources, "
        "and it is never evidence for product behavior.")


class PackError(Exception):
    """Raised when a pack cannot be loaded or used."""


@dataclass
class PackFile:
    path: str
    role: str
    sha256: str


@dataclass
class Pack:
    root: Path
    manifest: PackManifest
    files: list[PackFile] = field(default_factory=list)
    sha256: str = ""

    def record(self) -> dict:
        """What run.json stores: no local paths."""
        return {"name": self.manifest.name, "version": self.manifest.version, "sha256": self.sha256,
                "files": [{"path": f.path, "role": f.role, "sha256": f.sha256} for f in self.files]}


def _inside(root: Path, rel: str, *, folder: bool = False) -> Path:
    full = (root / rel).resolve()
    if not full.is_relative_to(root):
        raise PackError(f"{rel}: resolves outside the pack")
    if folder:
        if not full.is_dir():
            raise PackError(f"{rel}: folder not found")
    elif not full.is_file():
        raise PackError(f"{rel}: file not found")
    return full


def _hash(full: Path, rel: str) -> str:
    size = full.stat().st_size
    if size > MAX_FILE_BYTES:
        raise PackError(f"{rel}: larger than {MAX_FILE_BYTES} bytes")
    return hashlib.sha256(full.read_bytes()).hexdigest()


def load_pack(folder: Path) -> Pack:
    root = folder.resolve()
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        raise PackError(f"no {MANIFEST} in {folder}")
    if manifest_path.resolve() != manifest_path:
        raise PackError(f"{MANIFEST} must not be a symlink")
    raw_bytes = manifest_path.read_bytes()
    if len(raw_bytes) > MAX_FILE_BYTES:
        raise PackError(f"{MANIFEST} is larger than {MAX_FILE_BYTES} bytes")
    try:
        raw = yaml.safe_load(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise PackError(f"{MANIFEST} is not valid YAML: {exc}") from None
    if not isinstance(raw, dict):
        raise PackError(f"{MANIFEST} must contain a mapping")
    try:
        manifest = PackManifest.model_validate(raw)
    except ValidationError as exc:
        lines = [f"{MANIFEST} is invalid:"]
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"]) or "(root)"
            lines.append(f"  - {loc}: {err['msg']}")
        raise PackError("\n".join(lines)) from None

    named: list[tuple[str, str]] = [(MANIFEST, "manifest")]
    if manifest.conventions:
        named.append((manifest.conventions, "conventions"))
    named += [(r.path, "reference") for r in manifest.references]
    named += [(s.path, "article_spec") for s in manifest.article_specs]
    named += [(c.path, "cleanup_step") for c in manifest.cleanup_steps if c.path]
    named += [(c.path, "capture_profile") for c in manifest.capture_profiles]
    if manifest.vale:
        styles = _inside(root, manifest.vale.styles_path, folder=True)
        for style in manifest.vale.based_on:
            if not (styles / style).is_dir():
                raise PackError(f"vale: style folder {manifest.vale.styles_path.rstrip('/')}/{style} not found")
        for item in sorted(styles.rglob("*")):
            if item.is_file() or item.is_symlink():
                rel = (Path(manifest.vale.styles_path) / item.relative_to(styles)).as_posix()
                named.append((rel, "vale_style"))

    files: dict[str, PackFile] = {}
    total = 0
    for rel, role in named:
        if rel in files:
            if files[rel].role != role:
                raise PackError(f"{rel}: listed as both {files[rel].role} and {role}")
            continue
        full = _inside(root, rel)
        digest = _hash(full, rel)
        total += full.stat().st_size
        files[rel] = PackFile(rel, role, digest)
    if len(files) > MAX_FILES:
        raise PackError(f"more than {MAX_FILES} files")
    if total > MAX_PACK_BYTES:
        raise PackError(f"larger than {MAX_PACK_BYTES} bytes in total")
    ordered = sorted(files.values(), key=lambda f: f.path)
    digest = hashlib.sha256("".join(f"{f.path}\0{f.role}\0{f.sha256}\n" for f in ordered).encode()).hexdigest()
    return Pack(root, manifest, ordered, digest)


def resolve_pack(config: DocForgeConfig, config_path: Path, name: str) -> Path:
    """The folder of a named pack, relative to the docforge.yaml that names it."""
    ref = config.packs.get(name)
    if ref is None:
        known = ", ".join(sorted(config.packs)) or "none"
        raise PackError(f"pack {name!r} is not in {config_path} (defined: {known})")
    folder = Path(ref.path).expanduser()
    return folder if folder.is_absolute() else (config_path.parent / folder)


COPIED_ROLES = ("manifest", "conventions", "reference", "article_spec", "vale_style")


def check_product(pack: Pack, product: str | None) -> None:
    keys = [p.key for p in pack.manifest.products]
    if product is not None and product not in keys:
        raise PackError(f"product {product!r} is not in pack {pack.manifest.name} "
                        f"(products: {', '.join(keys) or 'none'})")


def copy_into_run(pack: Pack, run: Path, product: str | None = None) -> dict:
    """Copy the files stages and lint use into <run>/pack/. Returns the run.json record."""
    check_product(pack, product)
    target = run / RUN_FOLDER
    for f in pack.files:
        if f.role in COPIED_ROLES:
            dest = target / f.path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pack.root / f.path, dest)
    record = pack.record()
    record["copied_to"] = RUN_FOLDER
    if product is not None:
        record["product"] = product
    return record


# --- work orders -------------------------------------------------------------


def _ref(base: str, path: str) -> str:
    return f"`{base}/{RUN_FOLDER}/{path}`"


def stage_lines(manifest: PackManifest, record: dict, stage: str, deliverables: list[str], base: str) -> list[str]:
    """Work-order lines for one stage ("revision" reads like the Drafter). `base` names the run folder."""
    if stage not in STAGES + ("revision",):
        return []
    read_stage = "drafter" if stage == "revision" else stage
    lines = ["", f"## House pack: {record['name']} {record['version']}", "",
             f"Pack sha256 `{record['sha256'][:12]}...`. {RULE}", ""]
    if manifest.conventions:
        lines.append(f"- Output conventions: {_ref(base, manifest.conventions)}")
    product = record.get("product")
    if product:
        title = next((p.title for p in manifest.products if p.key == product), product)
        lines.append(f"- Product: {title} (`{product}`)")
    elif manifest.products:
        lines.append("- Product: not chosen, so product references are left out. Pack products: "
                     + ", ".join(f"`{p.key}`" for p in manifest.products))
    refs = [r for r in manifest.references if read_stage in r.stages
            and (not r.products or product in r.products)
            and (stage == "analyzer" or any(applies(r.applies_to, d) for d in deliverables))]
    lines += [f"- Reference: {r.title}, {_ref(base, r.path)}" for r in refs]
    if stage == "analyzer":
        if manifest.article_specs:
            lines += ["", "Article structure specs. Record in the content plan which spec each deliverable follows:", ""]
            for spec in manifest.article_specs:
                scope = f" (for {', '.join(spec.applies_to)})" if spec.applies_to else ""
                lines.append(f"- `{spec.type}`{': ' + spec.title if spec.title else ''}{scope}: {_ref(base, spec.path)}")
    else:
        for d in deliverables:
            specs = [s for s in manifest.article_specs if s.applies_to and applies(s.applies_to, d)]
            if specs:
                lines.append(f"- `{d}` follows the `{specs[0].type}` spec: {_ref(base, specs[0].path)}")
        if stage == "drafter":
            lines += ["", "Follow the conventions and each deliverable's spec for format and structure. "
                          "Where they conflict with the sources, the sources win; record the conflict in the "
                          "clarification register."]
        elif stage == "proofreader":
            lines += ["", "Check each deliverable against the conventions and its spec. Report every deviation "
                          "in `qa/QA-REPORT.md` with the pack file and section it breaks."]
    if len(lines) == 5:
        return []
    return lines


def run_manifest(run: Path, record: dict) -> PackManifest:
    """Read and check the pack.yaml copied into a run against the hash recorded in run.json."""
    path = run / record.get("copied_to", RUN_FOLDER) / MANIFEST
    expected = next((f["sha256"] for f in record.get("files", []) if f["path"] == MANIFEST), None)
    try:
        data = path.read_bytes()
    except OSError:
        raise PackError(f"{path} is missing") from None
    if hashlib.sha256(data).hexdigest() != expected:
        raise PackError(f"{path} does not match the hash recorded in run.json")
    return PackManifest.model_validate(yaml.safe_load(data.decode("utf-8")))


def run_vale_styles(run: Path, record: dict) -> list[tuple[str, Path]]:
    """(style name, folder) for each pack Vale style copied into a run, after checking every file's hash."""
    manifest = run_manifest(run, record)
    if manifest.vale is None:
        return []
    base = run / record.get("copied_to", RUN_FOLDER)
    for f in record.get("files", []):
        if f["role"] != "vale_style":
            continue
        path = base / f["path"]
        try:
            data = path.read_bytes()
        except OSError:
            raise PackError(f"{path} is missing; start the run again with the pack") from None
        if hashlib.sha256(data).hexdigest() != f["sha256"]:
            raise PackError(f"{path} does not match the hash recorded in run.json")
    styles = base / manifest.vale.styles_path
    return [(name, styles / name) for name in manifest.vale.based_on]


def run_pack_files(manifest: PackManifest, record: dict) -> list[tuple[str, str]]:
    """(role, path) for every pack file any stage of this run reads: conventions, the references for the
    run's product (or with no product limit), and every article spec. Order is stable."""
    product = record.get("product")
    files: list[tuple[str, str]] = []
    if manifest.conventions:
        files.append(("conventions", manifest.conventions))
    files += [("reference", r.path) for r in manifest.references if not r.products or product in r.products]
    files += [("article_spec", s.path) for s in manifest.article_specs]
    return files
