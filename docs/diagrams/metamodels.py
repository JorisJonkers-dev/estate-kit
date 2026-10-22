"""Class diagrams of deploy-kit's Ecore metamodels, one per concept, marked with
what estate-kit changes. Run from this directory with the deploy-kit checkout
path, then build.py:  python3 metamodels.py ../../../deploy-kit"""
import sys
import xml.etree.ElementTree as ET

from gen import Graph, classes as classes_diagram, write_all

XT = "{http://www.w3.org/2001/XMLSchema-instance}type"
TONE = {"changed": "warn", "removed": "bad", "new": "good"}

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
            mult = ("1..*" if lo == "1" else "0..*") if up == "-1" else ("1" if lo == "1" else "0..1")
            if s.get(XT) == "ecore:EReference":
                refs.append((s.get("name"), t, s.get("containment") == "true", mult))
            else:
                attrs.append(f"{s.get('name')}: {t}" + (" [*]" if up == "-1" else ""))
        sup = [x.split("//")[-1] for x in (c.get("eSuperTypes") or "").split()]
        out[c.get("name")] = {"abstract": c.get("abstract") == "true", "super": sup, "attrs": attrs, "refs": refs}
    return out


def draw(name, title, names, classes, extra_refs=None, direction="LR"):
    extra_refs = extra_refs or {}
    members = [n for n in names if n in classes]
    present = set(members)
    body, relations, tones, notes = [], [], {}, []
    for n in members:
        c = classes[n]
        lines = list(c["attrs"][:8])
        for rname, t, cont, mult in c["refs"] + extra_refs.get(n, []):
            if t in present and t != n:
                relations.append((n, t, "comp" if cont else "assoc", rname, mult))
            elif not cont:
                lines.append(f"{rname}: {t} [{mult}]")
        for sup in c["super"]:
            if sup in present:
                relations.append((n, sup, "inherit"))
            else:
                lines.insert(0, f"extends {sup}")
        body.append((n, "abstract" if c["abstract"] else None, lines))
        status = CHANGES.get(n) or (("new", "added by estate-kit") if n in NEW else None)
        if status:
            tones[n] = TONE[status[0]]
            notes.append((n, f"{status[0]}: {status[1]}"))
    if tones:
        notes.append(("", "Key: amber is changed, red is removed, green is new; the rest carries over"))
    classes_diagram(name, title, body, relations, tones=tones, direction=direction, notes=notes)


def draw_hierarchy(name, title, names, classes, per_row=6):
    """A parent with many subclasses: the parent on top and the subclasses in a grid below it,
    every generalization sharing one trunk. A layered layout would put them all in one rank."""
    g = Graph(name, title, placed=True)
    parent, leaves = names[0], [n for n in names[1:] if n in classes]
    w, gap = 230, 30
    width = per_row * w + (per_row - 1) * gap
    c = classes[parent]
    g.uml_class(parent, parent, c["attrs"], (width - w) // 2, 0, w, "abstract" if c["abstract"] else None)
    # Every generalization leaves its class on the left, just under the name, runs up the gap
    # left of its column to a bus under the parent, and joins the parent from below.
    bus, centre = 170, width / 2
    y = 220
    for row in range(0, len(leaves), per_row):
        chunk = leaves[row:row + per_row]
        tallest = 0
        for i, n in enumerate(chunk):
            lines = classes[n]["attrs"][:6]
            status = CHANGES.get(n) or (("new", "added by estate-kit") if n in NEW else None)
            x = i * (w + gap)
            g.uml_class(n, n, lines, x, y, w, tone=TONE[status[0]] if status else "plain")
            h = 28 + 22 * max(1, len(lines)) + 8
            channel = x - gap / 2
            g.generalize(n, parent, [(channel, y + 14), (channel, bus), (centre, bus)], exit_y=14 / h)
            tallest = max(tallest, h)
        y += tallest + 40
    g.done()


if __name__ == "__main__":
    base = sys.argv[1] + "/emf/bundles/metamodel/model/"
    every = {}
    for f, groups in GROUPS.items():
        classes = parse(base + f)
        every.update(classes)
        for name, title, names in groups:
            if name == "mm-deliverables":
                draw_hierarchy(name, title, names, classes)
            else:
                draw(name, title, names, classes)
    every.update(NEW)
    for name, title, names, extra in NEW_GROUPS:
        draw(name, title, names, every, extra)
    write_all("raw")
