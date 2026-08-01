const timeoutFetch = async (url, options = {}, timeout = 10000) => {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(timeout), headers: { 'user-agent': 'CompanyHunter/1.0 (personal job research)', ...options.headers } });
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response;
};
const domainName = (url) => new URL(url).hostname.replace(/^www\./, '');
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
    const url = text.match(/https?:\/\/[^\s"<>]+/i)?.[0]?.replace(/[.,)]+$/, '');
    if (!region || !url) return [];
    try {
      const name = text.slice(0, text.indexOf(url)).split(/\s+(?:is|are|[-—|])/i)[0].trim().slice(0, 100) || domainName(url);
      return [{ name, website: url, domain: domainName(url), region, source: 'hacker_news' }];
    } catch { return []; }
  });
}

export async function discoverYc(config) {
  const base = 'https://www.ycombinator.com';
  const industries = ['Developer%20Tools', 'Infrastructure', 'B2B', 'Artificial%20Intelligence'];
  const pages = await Promise.all(industries.map((industry) => timeoutFetch(`${base}/companies/industry/${industry}`, {}, 10000).then((res) => res.text()).catch(() => '')));
  const slugs = [...new Set(pages.flatMap((html) => [...html.matchAll(/href=["'](\/companies\/(?!industry\/)[^"'?#]+)/gi)].map((match) => match[1])))].slice(0, config.limits.ycCompanies);
  const profiles = await Promise.all(slugs.map(async (slug) => {
    const html = await timeoutFetch(`${base}${slug}`, {}, 10000).then((res) => res.text()).catch(() => '');
    const text = htmlToText(html);
    const city = [...config.regions.usaCities, ...config.regions.europeanCities].find((item) => text.toLowerCase().includes(item.toLowerCase()));
    if (!city) return null;
    const region = config.regions.usaCities.includes(city) ? 'USA' : 'Europe';
    const website = [...html.matchAll(/href=["'](https?:\/\/[^"']+)/gi)].map((match) => match[1]).find((url) => !/(ycombinator|linkedin|twitter|x\.com|github|youtube|facebook)/i.test(new URL(url).hostname));
    if (!website) return null;
    const title = html.match(/<title>\s*(.*?)\s*-\s*Y Combinator/i)?.[1]?.replace(/<[^>]+>/g, '').trim() ?? slug.split('/').pop().replaceAll('-', ' ');
    return { name: title, website, domain: domainName(website), city, region, source: 'yc' };
  }));
  return profiles.filter(Boolean);
}
