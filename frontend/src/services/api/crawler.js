import { requestJson } from './client';

export async function crawlCompanySite(url, maxPages = 20) {
  return requestJson('/crawler/crawl', {
    method: 'POST',
    body: { url, max_pages: maxPages },
  }, 'Website crawl failed');
}

export async function getCrawlRuns() {
  return requestJson('/crawler/runs', {}, 'Could not load previous crawls');
}

export async function getCrawlRun(id) {
  return requestJson(`/crawler/runs/${encodeURIComponent(id)}`, {}, 'Could not load crawl details');
}
