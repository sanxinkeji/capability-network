function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function inlineMarkdown(text: string): string {
  return text
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

export function renderMarkdown(source: string): string {
  const lines = source.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inList = false

  const closeList = () => {
    if (inList) {
      html.push('</ul>')
      inList = false
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd()
    const trimmed = line.trim()

    if (!trimmed) {
      closeList()
      continue
    }

    if (trimmed.startsWith('### ')) {
      closeList()
      html.push(`<h3>${inlineMarkdown(escapeHtml(trimmed.slice(4)))}</h3>`)
      continue
    }
    if (trimmed.startsWith('## ')) {
      closeList()
      html.push(`<h2>${inlineMarkdown(escapeHtml(trimmed.slice(3)))}</h2>`)
      continue
    }
    if (trimmed.startsWith('# ')) {
      closeList()
      html.push(`<h1>${inlineMarkdown(escapeHtml(trimmed.slice(2)))}</h1>`)
      continue
    }
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) {
        html.push('<ul>')
        inList = true
      }
      html.push(`<li>${inlineMarkdown(escapeHtml(trimmed.slice(2)))}</li>`)
      continue
    }

    closeList()
    html.push(`<p>${inlineMarkdown(escapeHtml(trimmed))}</p>`)
  }

  closeList()
  return html.join('\n')
}
