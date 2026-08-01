const timeoutFetch = async (url, options = {}, timeout = 10000) => {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(timeout), headers: { 'user-agent': 'CompanyHunter/1.0 (personal job research)', ...options.headers } });
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response;
};
const domainName = (url) => new URL(url).hostname.replace(/^www\./, '');
const nonCompanyHost = /(?:ycombinator|linkedin|twitter|x\.com|github|youtube|facebook|instagram|tiktok|plus\.google|google\.com|gstatic|maps\.google|apple\.com|play\.google)/i;
const isCompanyUrl = (url) => {
  try { return !nonCompanyHost.test(new URL(url).hostname); } catch { return false; }
};
const htmlToText = (html) => html.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ');
const regionFromText = (text) => {
  const value = ` ${text.toLowerCase()} `;
  if (/\b(usa|u\.s\.|united states|us-only)\b/.test(value)) return 'USA';
  if (/\b(europe|european|european union|eu|united kingdom|uk|germany|france|netherlands|spain|portugal|ireland|sweden|denmark|finland|poland)\b/.test(value)) return 'Europe';
  return '';
};

export async function discoverHackerNews(config) {
  const api = 'https://hacker-news.firebaseio.com/v0';
  const getJson = async (endpoint) => (await timeoutFetch(`${api}/${endpoint}.json`, {}, 8000)).json();
  const askIds = (await getJson('askstories')).slice(0, 100);
  const stories = await Promise.all(askIds.map((id) => getJson(`item/${id}`).catch(() => null)));
  const thread = stories.find((story) => story?.title?.toLowerCase().includes('who is hiring'));
  if (!thread) return [];
  const comments = await Promise.all((thread.kids ?? []).slice(0, config.limits.hnComments).map((id) => getJson(`item/${id}`).catch(() => null)));
  return comments.flatMap((comment) => {
    const text = htmlToText(comment?.text ?? '');
    const region = regionFromText(text);
    const url = [...text.matchAll(/https?:\/\/[^\s"<>]+/gi)].map((match) => match[0].replace(/[.,)]+$/, '')).find(isCompanyUrl);
    if (!region || !url) return [];
    try {
      const name = text.slice(0, text.indexOf(url)).split(/\s+(?:is|are|[-—|])/i)[0].trim().slice(0, 100) || domainName(url);
      return [{ name, website: url, domain: domainName(url), region, source: 'hacker_news' }];
    } catch { return []; }
  });
}

export async function discoverYc(config) {
  // This is a community-maintained daily JSON mirror of YC's public directory.
  // Unlike page scraping, it supplies canonical websites, locations and hiring
  // flags directly, so social links cannot accidentally enter the crawl queue.
  const companies = await timeoutFetch('https://yc-oss.github.io/api/companies/hiring.json', {}, 15000).then((res) => res.json());
  return companies
    .filter((company) => company.website && isCompanyUrl(company.website))
    .map((company) => {
      const location = company.all_locations ?? '';
      const city = [...config.regions.usaCities, ...config.regions.europeanCities]
        .find((item) => location.toLowerCase().includes(item.toLowerCase())) ?? '';
      const us = /united states|\busa\b/i.test(location) || company.regions?.includes('United States of America');
      const europe = /united kingdom|ireland|germany|netherlands|france|spain|portugal|sweden|denmark|finland|poland|estonia|switzerland|austria|europe/i.test(location) || company.regions?.some((region) => /europe/i.test(region));
      const region = us ? 'USA' : europe ? 'Europe' : '';
      return { name: company.name, website: company.website, domain: domainName(company.website), city, region, source: 'yc', launchedAt: company.launched_at ?? 0 };
    })
    .filter((company) => company.region)
    .sort((a, b) => b.launchedAt - a.launchedAt)
    .slice(0, config.limits.ycCompanies);
}
