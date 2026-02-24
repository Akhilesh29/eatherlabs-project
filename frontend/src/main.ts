import './style.css'

const API = '' // same origin; Vite proxies /api to backend

function el<T extends keyof HTMLElementTagNameMap>(tag: T, attrs: Record<string, string> = {}, children: (Node | string)[] = []): HTMLElementTagNameMap[T] {
  const e = document.createElement(tag)
  Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v))
  children.forEach(c => e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c))
  return e
}

function section(title: string, content: (HTMLElement | string)[]) {
  const s = el('section')
  s.appendChild(el('h2', {}, [title]))
  content.forEach(c => s.appendChild(typeof c === 'string' ? document.createTextNode(c) : c))
  return s
}

async function upload(files: FileList | null): Promise<{ parsed?: { file_id: string; filename: string; doc_type: string; extracted: unknown }[]; error?: string }> {
  if (!files?.length) return { error: 'No files selected' }
  const fd = new FormData()
  for (let i = 0; i < files.length; i++) fd.append('files', files[i])
  const r = await fetch(`${API}/api/documents/upload`, { method: 'POST', body: fd })
  if (!r.ok) return { error: `Upload failed: ${r.status}` }
  return r.json()
}

async function listDocs(): Promise<{ documents: { file_id: string; filename: string; doc_type: string; extracted: unknown }[] }> {
  const r = await fetch(`${API}/api/documents/list`)
  if (!r.ok) return { documents: [] }
  return r.json()
}

async function compare(): Promise<{ total_documents: number; documents_consistent: number; contradictions: { title: string; description: string; sources: string[] }[]; summary?: string }> {
  const r = await fetch(`${API}/api/compare`)
  if (!r.ok) return { total_documents: 0, documents_consistent: 0, contradictions: [] }
  return r.json()
}

async function generateReport(): Promise<{ job_id?: string; json_url?: string; txt_url?: string; summary?: string; contradiction_count?: number; error?: string }> {
  const r = await fetch(`${API}/api/report/generate`, { method: 'POST' })
  const j = await r.json()
  return j
}

function render() {
  const app = document.querySelector<HTMLDivElement>('#app')!
  app.innerHTML = ''
  app.appendChild(el('h1', {}, ['Document Verification Engine']))

  // 1. Upload
  const fileInput = el('input', { type: 'file', accept: '.pdf,.xlsx,.xls', multiple: 'true' })
  const uploadStatus = el('span', { class: 'status' })
  const uploadBtn = el('button', {}, ['Upload & Parse'])
  uploadBtn.onclick = async () => {
    uploadStatus.textContent = 'Uploading...'
    uploadStatus.className = 'status'
    const result = await upload(fileInput.files)
    if (result.error) {
      uploadStatus.textContent = result.error
      uploadStatus.className = 'status error'
    } else {
      uploadStatus.textContent = `Parsed ${result.parsed?.length ?? 0} file(s).`
      uploadStatus.className = 'status success'
      render()
    }
  }
  app.appendChild(section('1. Ingest documents', [
    el('div', {}, [
      fileInput,
      uploadBtn,
    ]),
    uploadStatus,
  ]))

  // 2. Parsed list (will be filled after load)
  const docList = el('ul', { class: 'doc-list' })
  const docSection = section('2. Parsed files', [docList])
  app.appendChild(docSection)

  async function refreshList() {
    const { documents } = await listDocs()
    docList.innerHTML = ''
    documents.forEach((d: { filename: string; doc_type: string }) => {
      const li = el('li', {}, [`${d.filename} (${d.doc_type})`])
      docList.appendChild(li)
    })
  }
  refreshList()

  // 3. Compare
  const compareStatus = el('span', { class: 'status' })
  const contradictionList = el('ul', { class: 'contradiction-list' })
  const compareBtn = el('button', {}, ['Compare documents'])
  compareBtn.onclick = async () => {
    compareStatus.textContent = 'Comparing...'
    compareStatus.className = 'status'
    const result = await compare()
    compareStatus.textContent = result.summary ?? `${result.total_documents} docs, ${result.contradictions?.length ?? 0} contradictions`
    compareStatus.className = 'status'
    contradictionList.innerHTML = ''
    ;(result.contradictions || []).forEach((c: { title: string; description: string; sources: string[] }) => {
      const li = el('li', {}, [
        el('strong', {}, [c.title]),
        el('div', {}, [c.description]),
        el('div', { class: 'status' }, [`Sources: ${(c.sources || []).join(', ')}`]),
      ])
      contradictionList.appendChild(li)
    })
  }
  app.appendChild(section('3. Contradictions', [compareBtn, compareStatus, contradictionList]))

  // 4. Report
  const reportStatus = el('span', { class: 'status' })
  const reportLinks = el('div', { class: 'report-actions' })
  const reportBtn = el('button', {}, ['Generate & download report'])
  reportBtn.onclick = async () => {
    reportStatus.textContent = 'Generating...'
    reportStatus.className = 'status'
    reportLinks.innerHTML = ''
    const result = await generateReport()
    if (result.error) {
      reportStatus.textContent = result.error
      reportStatus.className = 'status error'
    } else {
      reportStatus.textContent = result.summary ?? `Report ${result.job_id} generated.`
      reportStatus.className = 'status success'
      if (result.json_url) {
        const a = el('a', { href: API + result.json_url, download: '' }, ['Download JSON'])
        reportLinks.appendChild(a)
      }
      if (result.txt_url) {
        const a = el('a', { href: API + result.txt_url, download: '' }, ['Download TXT'])
        reportLinks.appendChild(a)
      }
    }
  }
  app.appendChild(section('4. Report', [reportBtn, reportStatus, reportLinks]))
}

render()
