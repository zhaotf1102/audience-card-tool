import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function App() {
  const [job, setJob] = useState(null);
  const [categories, setCategories] = useState({});
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/categories`).then(r => r.json()).then(setCategories);
  }, []);

  const cards = job?.cards || [];
  const canCrop = cards.length > 0;
  const canGenerate = job?.template_uploaded && cards.some(card => card.crop_urls?.length);

  async function createJob() {
    setLoading(true);
    setMessage('正在创建项目...');
    try {
      const res = await fetch(`${API_BASE}/api/jobs`, { method: 'POST' });
      setJob(await res.json());
      setMessage('项目已创建，可以上传照片和 PPT 模板。');
      await refreshJobFromResponse(res);
    } finally {
      setLoading(false);
    }
  }

  async function refreshJob() {
    if (!job?.job_id) return;
    const res = await fetch(`${API_BASE}/api/jobs/${job.job_id}`);
    setJob(await res.json());
  }

  async function refreshJobFromResponse(res) {
    const data = await res.clone().json();
    if (data.job_id) {
      const next = await fetch(`${API_BASE}/api/jobs/${data.job_id}`);
      setJob(await next.json());
    }
  }

  async function uploadImages(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length || !job?.job_id) return;
    const form = new FormData();
    files.forEach(file => form.append('files', file));
    setLoading(true);
    setMessage('正在上传照片...');
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${job.job_id}/images`, { method: 'POST', body: form });
      setJob(await res.json());
      setMessage('照片已上传，请确认分类。');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  }

  async function uploadTemplate(e) {
    const file = e.target.files?.[0];
    if (!file || !job?.job_id) return;
    const form = new FormData();
    form.append('file', file);
    setLoading(true);
    setMessage('正在上传 PPT 模板...');
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${job.job_id}/template`, { method: 'POST', body: form });
      setJob(await res.json());
      setMessage('PPT 模板已上传。');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  }

  async function updateCategory(cardId, category) {
    const res = await fetch(`${API_BASE}/api/jobs/${job.job_id}/cards/${cardId}/category`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category }),
    });
    setJob(await res.json());
  }

  async function crop() {
    setLoading(true);
    setMessage('正在裁剪：9×3 → 左4×3 / 右5×3 ...');
    try {
      const form = new FormData();
      form.append('margin_ratio', '0.01');
      const res = await fetch(`${API_BASE}/api/jobs/${job.job_id}/crop`, { method: 'POST', body: form });
      setJob(await res.json());
      setMessage('裁剪完成，请检查预览。');
    } finally {
      setLoading(false);
    }
  }

  async function generatePpt() {
    setLoading(true);
    setMessage('正在生成 PPT...');
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${job.job_id}/ppt`, { method: 'POST' });
      const data = await res.json();
      setJob(data);
      setMessage('PPT 已生成。');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Audience Card Tool MVP</p>
          <h1>观众信息卡裁剪与 PPT 自动生成</h1>
          <p>先跑通核心流程：上传照片、人工确认分类、固定 9×3 裁剪、生成 PPT。</p>
        </div>
        <button onClick={createJob} disabled={loading}>{job ? '新建项目' : '创建项目'}</button>
      </header>

      {message && <div className="message">{loading ? '⏳ ' : '✅ '}{message}</div>}

      {job && (
        <section className="panel">
          <h2>当前项目</h2>
          <p className="muted">Job ID: {job.job_id}</p>
          <div className="actions">
            <label className="upload">
              上传总卡照片
              <input type="file" accept="image/*" multiple onChange={uploadImages} />
            </label>
            <label className="upload">
              上传 PPT 模板
              <input type="file" accept=".pptx" onChange={uploadTemplate} />
            </label>
            <button onClick={crop} disabled={!canCrop || loading}>开始裁剪</button>
            <button onClick={generatePpt} disabled={!canGenerate || loading}>生成 PPT</button>
            {job.output_pptx_url && (
              <a className="download" href={`${API_BASE}${job.output_pptx_url}`} target="_blank">下载新 PPT</a>
            )}
          </div>
        </section>
      )}

      {cards.length > 0 && (
        <section className="grid">
          {cards.map(card => (
            <article key={card.id} className="card">
              <img src={`${API_BASE}${card.image_url}`} alt={card.filename} />
              <h3>{card.filename}</h3>
              <select value={card.category || ''} onChange={e => updateCategory(card.id, e.target.value)}>
                <option value="">请选择分类</option>
                {Object.entries(categories).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              {card.crop_urls?.length > 0 && (
                <div className="crops">
                  {card.crop_urls.map(url => <img key={url} src={`${API_BASE}${url}`} alt="裁剪预览" />)}
                </div>
              )}
            </article>
          ))}
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
