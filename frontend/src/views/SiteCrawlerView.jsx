import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

function timestamp(value) {
  return value ? new Date(value).toLocaleString() : '—';
}

export default function SiteCrawlerView() {
  const [url, setUrl] = useState('https://example.com');
  const [maxPages, setMaxPages] = useState(20);
  const [run, setRun] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const refreshHistory = async () => {
    try { setHistory(await api.getCrawlRuns()); } catch { setHistory([]); }
  };

  useEffect(() => { refreshHistory(); }, []);

  const startCrawl = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setRun(null);
    try {
      const result = await api.crawlCompanySite(url, Number(maxPages));
      setRun(result);
      refreshHistory();
    } catch (err) {
      setError(err.message || 'Website crawl failed');
    } finally {
      setLoading(false);
    }
  };

  const openRun = async (id) => {
    try { setRun(await api.getCrawlRun(id)); setError(''); } catch (err) { setError(err.message); }
  };

  return (
    <div className="stack site-crawler">
      <section className="panel crawler-intro">
        <div className="panel-body">
          <span className="eyebrow">Website discovery</span>
          <h2>Company site crawler</h2>
          <p className="muted">Map public pages and collect page titles, descriptions, headings, links, and readable text previews.</p>
          <form className="crawler-form" onSubmit={startCrawl}>
            <label className="crawler-url-field">
              <span className="form-label">Company website URL</span>
              <input className="form-input" type="url" required value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://company.example" />
            </label>
            <label className="crawler-limit-field">
              <span className="form-label">Page limit</span>
              <select className="form-input" value={maxPages} onChange={(event) => setMaxPages(event.target.value)}>
                {[5, 10, 20, 35, 50].map((limit) => <option key={limit} value={limit}>{limit} pages</option>)}
              </select>
            </label>
            <button className="btn btn-primary crawler-submit" type="submit" disabled={loading}>{loading ? 'Crawling site…' : 'Start crawl'}</button>
          </form>
          <p className="crawler-note">Respects robots.txt, stays on the entered site, limits depth and page size, and stores results locally. Only public HTTP/HTTPS websites on standard ports are allowed. Private and local network targets are blocked.</p>
        </div>
      </section>

      {error && <div className="alertbar error"><span className="alert-title">Crawler error</span><span>{error}</span></div>}

      {run && (
        <>
          <div className="crawler-summary">
            <div className="kpi panel"><div className="kpi-label">URLs discovered</div><div className="kpi-value">{run.pages_discovered}</div><div className="kpi-sub">Same-origin links seen within crawl depth</div></div>
            <div className="kpi panel"><div className="kpi-label">Pages fetched</div><div className="kpi-value">{run.pages_crawled}</div><div className="kpi-sub">HTML and other public page responses</div></div>
            <div className="kpi panel"><div className="kpi-label">Fetch errors</div><div className="kpi-value">{run.pages_failed}</div><div className="kpi-sub">Blocked, unavailable, or failed pages</div></div>
            <div className="kpi panel"><div className="kpi-label">Run status</div><div className="kpi-value crawler-status">{run.status === 'COMPLETED' ? 'Complete' : 'With errors'}</div><div className="kpi-sub">{timestamp(run.completed_at)}</div></div>
          </div>
          <p className="crawler-note">{run.pages_skipped_robots} URL(s) skipped by robots.txt. Discovery counts same-origin URLs seen; it does not mean the whole site was crawled.</p>
          <section className="stack crawler-results">
            <div className="hstack-between"><h2>Pages from {run.origin}</h2><span className="tag tag-neutral">{run.pages?.length || 0} records</span></div>
            {(run.pages || []).map((page) => (
              <article className="panel crawler-page" key={page.url}>
                <div className="crawler-page-head">
                  <div><span className={`tag ${page.error ? 'reject' : 'approve'}`}>{page.http_status ?? 'ERROR'}</span><h3>{page.title || 'Untitled page'}</h3></div>
                  <a href={page.url} target="_blank" rel="noreferrer">Open page ↗</a>
                </div>
                <code className="crawler-url">{page.url}</code>
                {page.error ? <p className="crawler-description error-text">{page.error}</p> : <>
                  {page.description && <p className="crawler-description">{page.description}</p>}
                  {!!page.headings?.length && <div className="crawler-headings"><span className="section-label">Headings</span><div>{page.headings.slice(0, 8).map((heading, index) => <span key={`${heading}-${index}`}>{heading}</span>)}</div></div>}
                  {page.text_excerpt && <p className="crawler-excerpt">{page.text_excerpt}</p>}
                  <div className="crawler-foot"><span>{page.internal_links?.length || 0} links on page</span>{page.canonical_url && <span>Canonical: {page.canonical_url}</span>}</div>
                </>}
              </article>
            ))}
          </section>
        </>
      )}

      <section className="panel">
        <div className="panel-header"><span className="panel-title">Recent crawl history</span><button className="btn btn-secondary btn-sm" onClick={refreshHistory}>Refresh</button></div>
        {history.length ? <div className="table-wrap crawler-history"><table className="table"><thead><tr><th>Website</th><th>Status</th><th>Fetched / URLs seen</th><th>Started</th><th /></tr></thead><tbody>
          {history.map((item) => <tr key={item.id}><td>{item.origin}</td><td><span className={`tag ${item.pages_failed ? 'review' : 'approve'}`}>{item.status.replaceAll('_', ' ')}</span></td><td>{item.pages_crawled} / {item.pages_discovered}</td><td>{timestamp(item.started_at)}</td><td><button className="text-button" onClick={() => openRun(item.id)}>View</button></td></tr>)}
        </tbody></table></div> : <div className="empty-state">No crawls yet. Enter a company website to start.</div>}
      </section>
    </div>
  );
}
