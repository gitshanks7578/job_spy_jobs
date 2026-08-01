import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { discoverHackerNews, discoverYc } from './src/sources.js';
import { crawlCompanies } from './src/websiteCrawler.js';
import { dedupeCompanies, writeRunOutput } from './src/storage.js';

const root = path.dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(await fs.readFile(path.join(root, 'hunter.config.json'), 'utf8'));
const sample = process.argv.includes('--sample');

const sampleCompanies = [
  { name: 'GitLab', website: 'https://about.gitlab.com', city: 'San Francisco', region: 'USA', source: 'sample' },
  { name: 'PostHog', website: 'https://posthog.com', city: 'London', region: 'Europe', source: 'sample' },
  { name: 'Sentry', website: 'https://sentry.io', city: 'San Francisco', region: 'USA', source: 'sample' }
];

console.time('Company Hunter');
let discovered = sample ? sampleCompanies : [];
if (!sample) {
  const tasks = [];
  if (config.sources.includes('yc')) tasks.push(discoverYc(config));
  if (config.sources.includes('hackerNews')) tasks.push(discoverHackerNews(config));
  const results = await Promise.allSettled(tasks);
  for (const result of results) {
    if (result.status === 'fulfilled') discovered.push(...result.value);
    else console.warn(`Discovery source skipped: ${result.reason.message}`);
  }
}

const companies = dedupeCompanies(discovered);
console.log(`Discovered ${companies.length} unique companies. Crawling up to ${config.limits.companiesToCrawl}...`);
const crawl = await crawlCompanies(companies.slice(0, config.limits.companiesToCrawl), config);
await writeRunOutput(root, companies, crawl);
console.log(`Finished: ${companies.length} companies, ${crawl.jobs.length} hiring signals, ${crawl.failed.length} failed requests.`);
console.timeEnd('Company Hunter');
