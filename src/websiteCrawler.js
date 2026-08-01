import { PlaywrightCrawler, Configuration, log } from 'crawlee';

const wantedLink = /career|jobs?|hiring|join|about|team|engineering/i;
const keywords = /career|jobs?|hiring|intern(ship)?|junior|entry-level|graduate|remote/i;
const escape = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const score = (text, skills) => {
  const normalized = text.toLowerCase().replace(/\s+/g, ' ');
  const matched = [];
  for (const word of skills.mustHave) if (new RegExp(`(^|[^a-z0-9])${escape(word.toLowerCase())}($|[^a-z0-9])`, 'i').test(normalized)) matched.push({ word, points: 15 });
  for (const word of skills.techStack) if (new RegExp(`(^|[^a-z0-9])${escape(word.toLowerCase())}($|[^a-z0-9])`, 'i').test(normalized)) matched.push({ word, points: 5 });
  return { score: Math.min(100, matched.reduce((sum, item) => sum + item.points, 0)), matched: matched.map((item) => item.word) };
};
const priority = (value) => value >= 70 ? 'High' : value >= 40 ? 'Medium' : 'Low';

export async function crawlCompanies(companies, config) {
  const jobs = [], failed = [], companyData = new Map(companies.map((company) => [company.domain, { ...company, emails: [], phones: [], careersPage: '', linkedin: '', github: '', matchScore: 0, matchedKeywords: [] }]));
  const crawler = new PlaywrightCrawler({
    maxConcurrency: config.limits.maxConcurrency,
    maxRequestsPerCrawl: config.limits.maxRequests,
    // A daily discovery run benefits more from moving on than retrying every
    // blocked corporate site; failures are retained in failed.csv.
    maxRequestRetries: 0,
    requestHandlerTimeoutSecs: config.limits.requestTimeoutSeconds,
    navigationTimeoutSecs: config.limits.requestTimeoutSeconds,
    launchContext: { launchOptions: { headless: true } },
    async requestHandler({ request, page, enqueueLinks }) {
      const company = companyData.get(request.userData.domain);
      if (!company) return;
      await page.waitForLoadState('domcontentloaded');
      const text = (await page.locator('body').innerText()).slice(0, 100000);
      const html = await page.content();
      company.emails.push(...(text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) ?? []));
      company.phones.push(...(text.match(/(?:\+?\d[\d .()\-]{7,}\d)/g) ?? []));
      company.linkedin ||= html.match(/https?:\/\/[^"' ]*linkedin\.com[^"' ]*/i)?.[0] ?? '';
      company.github ||= html.match(/https?:\/\/[^"' ]*github\.com[^"' ]*/i)?.[0] ?? '';
      const result = score(text, config.skills);
      if (result.score > company.matchScore) { company.matchScore = result.score; company.matchedKeywords = result.matched; }
      if (keywords.test(text)) jobs.push({ name: company.name, domain: company.domain, pageUrl: request.url, matchScore: result.score, matchedKeywords: result.matched.join('; '), priority: priority(result.score) });
      if (request.userData.home) {
        const linkResult = await enqueueLinks({ selector: 'a', strategy: 'same-domain', limit: config.limits.pagesPerCompany, transformRequestFunction: (item) => wantedLink.test(item.url) ? { ...item, userData: { domain: company.domain, home: false } } : false });
        if (linkResult.processedRequests?.length) company.careersPage ||= linkResult.processedRequests[0].url;
      }
    },
    failedRequestHandler({ request, errorMessages }) {
      failed.push({ domain: request.userData.domain, url: request.url, reason: errorMessages?.at(-1) ?? request.errorMessages?.at(-1) ?? 'request_failed' });
    }
  }, new Configuration({ persistStorage: false }));
  await crawler.run(companies.map((company) => ({ url: company.website, userData: { domain: company.domain, home: true } })));
  for (const company of companyData.values()) { company.emails = [...new Set(company.emails)]; company.phones = [...new Set(company.phones)]; }
  log.info(`Crawled ${companyData.size} company homepages.`);
  return { companies: [...companyData.values()], jobs, failed };
}
