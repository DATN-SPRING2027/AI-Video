import { mkdir, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');
const vaultDir = join(projectRoot, 'graph-vault');
const outJson = join(projectRoot, 'assets', 'data', 'continuum-links.json');
const kgCli = join(projectRoot, '..', '..', '2d-3d-knowledge-graph', 'tools', 'links', 'cli.mjs');

const NOTES = [
  ['architecture/continuum-core.md', 'Continuum AI Core', ['architecture', 'core'], ['services/api-gateway', 'services/svc-iam', 'services/svc-task', 'services/svc-capture', 'services/svc-lifecycle', 'services/svc-chat', 'services/svc-handover', 'ai/sag-engine']],
  ['services/api-gateway.md', 'NestJS API Gateway', ['security', 'gateway'], ['security/pre-retrieval-acl', 'storage/redis-cluster', 'services/svc-iam']],
  ['security/pre-retrieval-acl.md', 'Pre-Retrieval Scoped ACL (P_eff)', ['security', 'acl'], ['ai/sag-engine', 'storage/lancedb-vectors', 'services/svc-iam', 'governance/continuum-audit']],
  ['services/svc-iam.md', 'IAM & Scoped RBAC', ['security', 'service'], ['security/pre-retrieval-acl', 'governance/continuum-audit']],
  ['services/svc-task.md', 'Task Service (continuum_task)', ['capture', 'service'], ['adr/adr-009-task-mongodb', 'adr/adr-003-db-per-service', 'notes/work-note-209']],
  ['services/svc-capture.md', 'Work Note Capture Service', ['capture', 'service'], ['notes/work-note-209', 'services/svc-lifecycle', 'storage/mongodb-rs0']],
  ['services/svc-lifecycle.md', 'SME Verification Inbox', ['governance', 'service'], ['notes/work-note-209', 'governance/sme-verified-active', 'governance/continuum-audit']],
  ['governance/sme-verified-active.md', 'ACTIVE Verified Truth', ['governance', 'verified'], ['ai/sag-engine', 'storage/lancedb-vectors', 'handover/onboarding-roadmap']],
  ['services/svc-chat.md', 'Grounded AI Assistant', ['ai', 'service'], ['ai/sag-engine', 'ai/session-context-graph', 'governance/knowledge-gap-14']],
  ['services/svc-handover.md', 'Handover Audio & Roadmap', ['handover', 'service'], ['handover/onboarding-roadmap', 'storage/cloudflare-r2', 'notes/work-note-209']],
  ['services/svc-ingestion.md', 'MinerU & Document Ingestion', ['ai', 'service'], ['storage/cloudflare-r2', 'storage/bullmq-workers', 'ai/sag-engine']],
  ['services/svc-notification.md', 'Realtime WSS Notification', ['service', 'realtime'], ['storage/redis-cluster', 'governance/knowledge-gap-14']],
  ['ai/sag-engine.md', 'SAG Evidence Engine', ['ai', 'rag'], ['storage/lancedb-vectors', 'ai/session-context-graph', 'adr/adr-003-db-per-service', 'governance/knowledge-gap-14']],
  ['ai/session-context-graph.md', 'Session-Context Zero-Mem', ['ai', 'rag'], ['services/svc-chat', 'ai/sag-engine']],
  ['storage/mongodb-rs0.md', 'MongoDB 7.0 Replica Set', ['storage', 'database'], ['adr/adr-003-db-per-service', 'governance/continuum-audit', 'services/svc-task']],
  ['storage/lancedb-vectors.md', 'LanceDB Derived Index', ['storage', 'ai'], ['ai/sag-engine', 'security/pre-retrieval-acl']],
  ['storage/redis-cluster.md', 'Redis 7.2 & SingleFlight', ['storage', 'realtime'], ['services/api-gateway', 'storage/bullmq-workers']],
  ['storage/bullmq-workers.md', 'BullMQ Async Pipelines', ['storage', 'worker'], ['services/svc-ingestion', 'services/svc-handover']],
  ['storage/cloudflare-r2.md', 'Cloudflare R2 Private Store', ['storage', 'security'], ['services/svc-ingestion', 'services/svc-handover']],
  ['adr/adr-003-db-per-service.md', 'ADR-003 Database-Per-Service', ['architecture', 'adr'], ['storage/mongodb-rs0', 'services/svc-task', 'governance/sme-verified-active']],
  ['adr/adr-009-task-mongodb.md', 'ADR-009 Internal Task Lifecycle', ['architecture', 'adr'], ['services/svc-task', 'notes/work-note-209']],
  ['notes/work-note-209.md', 'Work Note #WN-209', ['capture', 'note'], ['services/svc-lifecycle', 'governance/sme-verified-active', 'adr/adr-003-db-per-service']],
  ['governance/knowledge-gap-14.md', 'Knowledge Gap #KG-14', ['governance', 'gap'], ['handover/onboarding-roadmap', 'services/svc-handover']],
  ['handover/onboarding-roadmap.md', 'Successor Handover Pack', ['handover', 'roadmap'], ['governance/sme-verified-active', 'adr/adr-003-db-per-service', 'adr/adr-009-task-mongodb']],
  ['governance/continuum-audit.md', 'Immutable Audit Trail', ['governance', 'security'], ['storage/mongodb-rs0', 'services/svc-lifecycle']]
];

await mkdir(vaultDir, { recursive: true });
await mkdir(dirname(outJson), { recursive: true });

for (const [relPath, title, tags, links] of NOTES) {
  const full = join(vaultDir, relPath);
  await mkdir(dirname(full), { recursive: true });
  const linkLines = links.map((l) => `- Connects to [[${l}]]`).join('\n');
  const md = `---\ntitle: "${title}"\ntags: [${tags.join(', ')}]\n---\n# ${title}\n\n${linkLines}\n`;
  await writeFile(full, md, 'utf8');
}

execFileSync(process.execPath, [kgCli, vaultDir, '--out', outJson], { stdio: 'inherit' });
console.log('Continuum AI Knowledge Graph JSON ready:', outJson);

