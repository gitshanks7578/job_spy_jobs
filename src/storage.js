import fs from 'node:fs/promises';
import path from 'node:path';

const today = () => new Date().toISOString().slice(0, 10);
const quote = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
const writeCsv = async (file, rows, columns) => {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, `${columns.join(',')}\n${rows.map((row) => columns.map((column) => quote(row[column])).join(',')).join('\n')}\n`, 'utf8');
};
export const dedupeCompanies = (companies) => [...new Map(companies.filter((company) => company.website).map((company) => {
  const domain = company.domain || new URL(company.website).hostname.replace(/^www\./, '');
  return [domain, { ...company, domain }];
})).values()];

export async function writeRunOutput(root, discovered, crawl) {
  const stateFile = path.join(root, 'state', 'seen_companies.csv');
  const existing = new Map();
  try { for (const line of (await fs.readFile(stateFile, 'utf8')).trim().split('\n').slice(1)) { const [domain, firstSeen] = line.split(',').map((value) => value.replaceAll('"', '')); existing.set(domain, firstSeen); } } catch { /* first run */ }
  const date = today();
  const crawled = new Map(crawl.companies.map((company) => [company.domain, company]));
  const rows = discovered.map((company) => ({ ...company, ...(crawled.get(company.domain) ?? {}), firstSeen: existing.get(company.domain) ?? date, newToday: !existing.has(company.domain) }));
  await writeCsv(stateFile, rows.map((row) => ({ domain: row.domain, first_seen_date: row.firstSeen, last_seen_date: date })), ['domain', 'first_seen_date', 'last_seen_date']);
  const columns = ['name', 'website', 'domain', 'city', 'region', 'source', 'careersPage', 'emails', 'phones', 'linkedin', 'github', 'matchScore', 'matchedKeywords', 'firstSeen', 'newToday'];
  const jobColumns = ['name', 'domain', 'pageUrl', 'matchScore', 'matchedKeywords', 'priority'];
  const failColumns = ['domain', 'url', 'reason'];
  for (const dir of [path.join(root, 'output', 'latest'), path.join(root, 'output', date)]) {
    await writeCsv(path.join(dir, 'companies.csv'), rows.sort((a, b) => b.matchScore - a.matchScore), columns);
    await writeCsv(path.join(dir, 'new_today.csv'), rows.filter((row) => row.newToday), columns);
    await writeCsv(path.join(dir, 'jobs.csv'), crawl.jobs, jobColumns);
    await writeCsv(path.join(dir, 'contacts.csv'), rows.map((row) => ({ name: row.name, emails: (row.emails ?? []).join('; '), phones: (row.phones ?? []).join('; '), linkedin: row.linkedin, github: row.github })), ['name', 'emails', 'phones', 'linkedin', 'github']);
    await writeCsv(path.join(dir, 'failed.csv'), crawl.failed, failColumns);
  }
}
