"""Class diagrams of deploy-kit's Ecore metamodels, one per concept, marked with
what estate-kit changes. Run from this directory with the deploy-kit checkout
path:  python3 metamodels.py ../../../deploy-kit"""
import sys
import xml.etree.ElementTree as ET

from gen import D, ACCENT, BAD, GOOD, WARN, esc

XT = "{http://www.w3.org/2001/XMLSchema-instance}type"
STATUS = {"changed": WARN, "removed": BAD, "new": GOOD}
MIXINS = {"SharedIntent"}  # shown as an "extends" line, not an edge

# What estate-kit does to each class; anything unlisted is carried over as is.
CHANGES = {
    "ImagesLock": ("removed", "digests are sealed into the Intent Fragment"),
    "LockedImage": ("removed", "digests are sealed into the Intent Fragment"),
    "RollbackBackup": ("removed", "a Rollback relies on the scheduled backups (#557)"),
    "ClusterState": ("changed", "read live, digested into the render key"),
    "NodeContract": ("changed", "derived from Infrastructure Intent"),
    "Node": ("changed", "derived from Infrastructure Intent"),
    "HandoverLedger": ("removed", "no legacy path after the cutover"),
    "ServingLocation": ("removed", "no legacy path after the cutover"),
    "Platform": ("changed", "gains admittedProjects and uiRoles"),
    "FluxSource": ("changed", "one prod tag per Project"),
    "ArtifactSigner": ("changed", "a Vault Transit key"),
    "RenderedArtifacts": ("changed", "the registry is also the render cache"),
    "Application": ("changed", "gains mail: the Mailboxes it declares"),
    "Provenance": ("changed", "becomes the render key"),
    "InputDigest": ("changed", "becomes the render key"),
    "ResolvedPolicyJob": ("changed", "one per Project, in its own unit (#544)"),
    "ResolvedEvents": ("changed", "one per Project, in its own unit (#544)"),
    "VaultPolicyJob": ("changed", "built as the secret-job component"),
    "MigrationPolicy": ("changed", "runner built as the migration-runner component"),
}

GROUPS = {
    "project-intent.ecore": [
        ("mm-project", "Project Intent: Project, Application, Process",
         ["Project", "Application", "Process", "SharedIntent"]),
        ("mm-effective", "Effective Intent: after lowering", ["EffectiveProject", "EffectiveApplication", "Process"]),
        ("mm-process", "Project Intent: what a Process needs",
         ["Process", "Surface", "Placement", "DiskRequest", "GpuRequest", "Sidecar", "Volume", "Capacity"]),
        ("mm-process-reach", "Project Intent: what a Process reaches",
         ["Process", "VpnAttachment", "Egress", "LibraryMount", "ApiAccess", "ApiRule"]),
        ("mm-probes", "Project Intent: probes",
         ["ProbePolicy", "Probes", "NoProbes", "Probe", "HttpProbe", "TcpProbe"]),
        ("mm-exposure", "Project Intent: exposure and edges",
         ["Application", "Exposure", "Route", "RateLimit", "DependencyEdge", "Credentials", "Observability", "Scrape"]),
        ("mm-migration", "Project Intent: migration",
         ["Migration", "ManagedMigration", "SelfMigration", "NoMigration"]),
        ("mm-config", "Project Intent: configuration",
         ["EnvFile", "EnvVariable", "EnvValue", "EnvLiteral", "Placeholder", "Asset"]),
        ("mm-grants", "Project Intent: grants",
         ["Grant", "KvGrant", "KvKey", "PlainKey", "GeneratedKey", "Generate", "DatabaseGrant", "TransitGrant", "Rotation"]),
        ("mm-platform", "Platform Intent: the document",
         ["Platform", "PlatformMetadata", "Substrate", "Bootstrap", "HandoverLedger", "ServingLocation", "AdminLogin",
          "FluxSource", "RenderedArtifacts", "ArtifactSigner", "VaultState"]),
        ("mm-platform-policies", "Platform Intent: policies",
         ["Platform", "Tier", "DurabilityPolicies", "DurabilityPolicy", "OffClusterCopy", "DestinationRange",
          "EnginePolicies", "EnginePolicy"]),
        ("mm-platform-cadence", "Platform Intent: cadences",
         ["Platform", "MonitorCadence", "TelemetryPolicy", "ProbeCadence", "EphemeralPolicy"]),
        ("mm-platform-delivery", "Platform Intent: delivery and jobs",
         ["Platform", "DeliveryPolicy", "ApiAccessPolicy", "AnalysisPolicy", "VaultPolicyJob", "MigrationPolicy"]),
        ("mm-platform-providers", "Platform Intent: providers, VPN and GPUs",
         ["Platform", "Provider", "ProviderSurface", "VpnPolicy", "VpnSetting", "GpuVendor", "GpuVendorPolicy"]),
        ("mm-platform-libraries", "Platform Intent: libraries",
         ["Platform", "Library", "LibraryDeclaration", "LibraryGrant"]),
    ],
    "resolved-deployment.ecore": [
        ("mm-resolved", "Resolved Deployment: the root",
         ["ResolvedDeployment", "Provenance", "InputDigest", "ReconcileUnit", "ResolvedEvents", "ResolvedPolicyJob",
          "ResolvedCatalogJob"]),
        ("mm-resolved-catalog", "Resolved Deployment: the database catalog",
         ["ResolvedCatalogJob", "ResolvedCatalog", "CatalogAdmin", "CatalogDatabase"]),
        ("mm-resolved-application", "Resolved Deployment: an Application and its Release Gate",
         ["ResolvedApplication", "ResolvedScrape", "ResolvedMigration", "MigratedDatabase", "ReleaseGate",
          "GateMigration", "GateAnalysis", "GateMember"]),
        ("mm-resolved-process", "Resolved Deployment: a Process",
         ["ResolvedProcess", "ResolvedSurface", "ResolvedPlacement", "ResolvedVolume", "BackupPlan", "BackupPeer",
          "ResolvedSidecar", "WritablePath"]),
        ("mm-resolved-process-reach", "Resolved Deployment: what a Process reaches",
         ["ResolvedProcess", "ResolvedVpn", "ResolvedGpu", "ResolvedLibraryMount", "InternetEgress",
          "ResolvedApiAccess", "ResolvedApiRule", "AdmittedRange"]),
        ("mm-resolved-probes", "Resolved Deployment: probes",
         ["ResolvedProbe", "StartupProbe", "ProbeTarget", "HttpTarget", "TcpTarget"]),
        ("mm-resolved-grants", "Resolved Deployment: grants, edges and environment",
         ["ResolvedGrant", "ResolvedGeneratedKey", "PolicyPath", "ResolvedEdge", "PolicyPeer", "EnvEntry",
          "SecretReference", "ResolvedAsset"]),
        ("mm-resolved-exposure", "Resolved Deployment: exposure",
         ["ResolvedExposure", "ResolvedRoute", "MiddlewareStep"]),
        ("mm-deliverables", "Deliverable Set: every file kind",
         ["Deliverable", "NamespaceFile", "IndexFile", "WorkloadFile", "SwitchoverFile", "IdentityFile",
          "NetworkPolicyFile", "MigrationFile", "BudgetFile", "IngressRouteFile", "MonitorFile", "RbacFile",
          "ServiceFile", "LibraryFile", "AliasFile", "ClaimFile", "ConfigMapFile", "BackupFile", "SecretFile",
          "ConnectionFile", "VaultPolicyFile", "PolicyJobFile", "CatalogJobFile", "EventsFile", "GeneratedKeysFile",
          "VaultRoleFile"]),
    ],
    "pinned-inputs.ecore": [
        ("mm-pinned-nodes", "Pinned inputs: the node contract", ["NodeContract", "Node", "Allocatable", "Gpu", "Disk"]),
        ("mm-pinned-state", "Pinned inputs: images lock and ClusterState",
         ["ImagesLock", "LockedImage", "ClusterState", "Binding", "CurrentPlacement", "RollbackBackup"]),
        ("mm-pinned-proofs", "Pinned inputs: proofs and assets", ["MigrationProof", "ProvenApplication", "AssetFile"]),
    ],
}

# Classes estate-kit adds, in the same form the parser produces.
NEW = {
    "Mailbox": {"abstract": False, "super": [], "attrs": ["local: LocalPart"], "refs": []},
    "ResolvedMailbox": {"abstract": False, "super": [], "attrs": ["address: EmailAddress", "sharedBy: ApplicationId [*]"],
                        "refs": [("password", "ResolvedGeneratedKey", False, "1")]},
    "MailboxFile": {"abstract": False, "super": ["Deliverable"], "attrs": ["a Mailbox custom resource"], "refs": []},
    "AdmittedProject": {"abstract": False, "super": [], "attrs": ["project: ProjectName", "repositoryId: RepositoryId",
                                                                  "workflow: WorkflowRef"], "refs": []},
    "UiRole": {"abstract": False, "super": [], "attrs": ["group: IdpGroup", "role: Viewer | Operator | Admin"], "refs": []},
    "InfrastructureIntent": {"abstract": False, "super": [], "attrs": ["labelPrefix: String"],
                             "refs": [("sites", "Site", True, "1..*")]},
    "Site": {"abstract": False, "super": [], "attrs": ["name: SiteName", "timezone: TimeZone"],
             "refs": [("nodes", "HostNode", True, "1..*"), ("window", "MaintenanceWindow", True, "1")]},
    "HostNode": {"abstract": False, "super": [], "attrs": ["name: NodeName", "arch: Arch", "roles: HostRole [*]",
                                                           "totals, reserve", "capabilities, taints"],
                 "refs": [("gpus", "GpuSpec", True, "*"), ("disks", "DiskSpec", True, "*"),
                          ("window", "MaintenanceWindow", True, "0..1")]},
    "MaintenanceWindow": {"abstract": False, "super": [], "attrs": ["start: LocalTime", "end: LocalTime",
                                                                    "days: Weekday [*]"], "refs": []},
    "GpuSpec": {"abstract": False, "super": [], "attrs": ["vendor, model, class", "memoryMib: Int"], "refs": []},
    "DiskSpec": {"abstract": False, "super": [], "attrs": ["media: Media", "usableGib: Int"], "refs": []},
    "HostData": {"abstract": False, "super": [], "attrs": ["node: NodeName", "roles, labels, taints",
                                                           "services: HostService [*]", "window: MaintenanceWindow",
                                                           "rebootPolicy: RebootPolicy"], "refs": []},
}
NEW_GROUPS = [
    ("mm-new-mailbox", "New: Mailboxes", ["Application", "Mailbox", "ResolvedMailbox", "ResolvedGeneratedKey", "MailboxFile"],
     {"Application": [("mail", "Mailbox", True, "*")]}),
    ("mm-new-admission", "New: admission and UI roles", ["Platform", "AdmittedProject", "UiRole"],
     {"Platform": [("admittedProjects", "AdmittedProject", True, "*"), ("uiRoles", "UiRole", True, "*")]}),
    ("mm-new-infrastructure", "New: Infrastructure Intent",
     ["InfrastructureIntent", "Site", "HostNode", "MaintenanceWindow", "GpuSpec", "DiskSpec"], {}),
    ("mm-new-host-data", "New: host data, rendered per node", ["HostNode", "HostData", "MaintenanceWindow"],
     {"HostData": [("from", "HostNode", False, "1")]}),
]


def parse(path):
    root = ET.parse(path).getroot()
    out = {}
    for c in root.findall("eClassifiers"):
        if c.get(XT) != "ecore:EClass":
            continue
        attrs, refs = [], []
        for s in c.findall("eStructuralFeatures"):
            t = (s.get("eType") or "").split("//")[-1].replace("EString", "String").replace("EInt", "Int") \
                .replace("EBoolean", "Bool").replace("ELong", "Long")
            up = s.get("upperBound")
            lo = s.get("lowerBound", "0")
            mult = "*" if up == "-1" else ("1" if lo == "1" else "0..1")
            if s.get(XT) == "ecore:EReference":
                refs.append((s.get("name"), t, s.get("containment") == "true", mult))
            else:
                attrs.append(f"{s.get('name')}: {t}" + (" [*]" if up == "-1" else ""))
        sup = [x.split("//")[-1] for x in (c.get("eSuperTypes") or "").split()]
        out[c.get("name")] = {"abstract": c.get("abstract") == "true", "super": sup, "attrs": attrs, "refs": refs}
    return out


def draw(name, title, names, classes, extra_refs=None, compact=False):
    d = D()
    extra_refs = extra_refs or {}
    members = [n for n in names if n in classes]
    present = set(members)
    # Tree layout: containment and inheritance edges go one column to the right.
    children = {n: [] for n in members}
    edges = []
    for n in members:
        for rname, t, cont, mult in classes[n]["refs"] + extra_refs.get(n, []):
            if t in present and t != n:
                edges.append((n, t, f"{rname} {mult}", "comp" if cont else "dep"))
                children[n].append(t)
        for s in classes[n]["super"]:
            if s in present and s not in MIXINS:
                edges.append((n, s, "", "inherit"))
                children[s].append(n)
    level, order = {}, []
    for n in members:
        if n in level:
            continue
        level[n] = 0 if not any(n in v for v in children.values()) else level.get(n, 0)
        stack = [n]
        while stack:
            p = stack.pop(0)
            if p not in order:
                order.append(p)
            for c in children[p]:
                if c not in level or level[c] <= level[p]:
                    if c not in order:
                        level[c] = level[p] + 1
                        stack.append(c)
    cols = {}
    for n in order:
        cols.setdefault(level[n], []).append(n)
    ids = {}
    W, GAP, VGAP = (220, 70, 18) if compact else (330, 150, 26)
    d.v(title, "text;fontSize=18;fontStyle=1;align=left;", 20, 10, 900, 30)
    ncols = max(cols) + 1 if cols else 1
    if compact:
        # A hierarchy with many leaves: the parent on top, leaves in a grid.
        per_row = 5
        leaves = [n for n in order if level[n] > 0]
        top = [n for n in order if level[n] == 0]
        for i, n in enumerate(top):
            ids[n] = box(d, n, classes[n], 20 + 2 * (W + GAP), 60, W)
        for i, n in enumerate(leaves):
            ids[n] = box(d, n, classes[n], 20 + (i % per_row) * (W + GAP), 220 + (i // per_row) * 80, W, names_only=True)
    else:
        for c in range(ncols):
            y = 60
            for n in cols.get(c, []):
                ids[n] = box(d, n, classes[n], 20 + c * (W + GAP), y, W)
                y += height(classes[n]) + VGAP
    styles = {
        "comp": "edgeStyle=orthogonalEdgeStyle;rounded=1;startArrow=diamondThin;startFill=1;startSize=16;endArrow=open;endSize=10;fontSize=12;",
        "dep": "edgeStyle=orthogonalEdgeStyle;rounded=1;endArrow=open;dashed=1;endSize=10;fontSize=12;",
        "inherit": "edgeStyle=orthogonalEdgeStyle;rounded=1;endArrow=block;endFill=0;endSize=14;",
    }
    for a, b, label, kind in edges:
        if a in ids and b in ids:
            if kind == "inherit":
                d.e(ids[a], ids[b], "", styles[kind] + ("exitX=0.5;exitY=0;entryX=0.5;entryY=1;" if compact else "exitX=0;exitY=0.5;entryX=1;entryY=0.5;"))
            else:
                d.e(ids[a], ids[b], label, styles[kind] + "exitX=1;exitY=0.5;entryX=0;entryY=0.5;", lx=0.75)
    legend(d, 20 + max(ncols, 1) * (W + GAP) if not compact else 20 + 5 * (W + GAP), 60)
    d.save(name)


def height(c):
    lines = len(c["attrs"][:8]) + len([r for r in c["refs"] if not r[2]][:4]) + (1 if c["super"] else 0)
    return 44 + lines * 20 + (16 if lines else 0)


def box(d, n, c, x, y, w, names_only=False):
    status = CHANGES.get(n) or (("new", "added by estate-kit") if n in NEW else None)
    head = ("&lt;&lt;abstract&gt;&gt;<br>" if c["abstract"] else "") + "<b>" + n + "</b>"
    if names_only:
        style = "rounded=0;" + (STATUS[status[0]] if status else "")
        return d.v(head, style, x, y, w, 56)
    lines = (["<i>extends " + ", ".join(c["super"]) + "</i>"] if c["super"] else []) + [esc(a) for a in c["attrs"][:8]] + [esc(f"{r[0]}: {r[1]} {r[3]}") for r in c["refs"] if not r[2]][:4]
    if status:
        lines.append("<i>" + esc(status[0] + ": " + status[1]) + "</i>")
    label = head + ("<hr>" + "<br>".join(lines) if lines else "")
    style = "rounded=0;align=left;verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=13;" + (STATUS[status[0]] if status else "")
    return d.v(label, style, x, y, w, height(c) + (20 if status else 0))


def legend(d, x, y):
    d.v("<b>Legend</b><br>carried over<br>changed<br>removed<br>new", "rounded=0;align=left;verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=13;", x, y, 140, 112)
    for i, (k, s) in enumerate([("changed", WARN), ("removed", BAD), ("new", GOOD)]):
        d.v("", "rounded=0;" + s, x + 150, y + 44 + i * 20, 18, 14)


if __name__ == "__main__":
    base = sys.argv[1] + "/emf/bundles/metamodel/model/"
    every = {}
    for f, groups in GROUPS.items():
        classes = parse(base + f)
        every.update(classes)
        for name, title, names in groups:
            draw(name, title, names, classes, compact=(name == "mm-deliverables"))
    every.update(NEW)
    for name, title, names, extra in NEW_GROUPS:
        draw(name, title, names, every, extra)
