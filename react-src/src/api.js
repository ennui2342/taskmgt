async function req(path, options) {
  const res = await fetch(path, options)
  if (!res.ok) throw new Error(`${options?.method ?? 'GET'} ${path} → ${res.status}`)
  if (res.status === 204) return null
  return res.json()
}

const json = body => ({
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})


// UTF-8-safe base64: handles multi-byte chars (e.g. §) that btoa alone cannot encode
const b64 = s => btoa(unescape(encodeURIComponent(s)))

export const api = {
  tasks: {
    list:   (filter, showClosed = false) => {
      if (filter === '^inbox') return req('/tasks?inbox=1')
      const params = new URLSearchParams()
      if (filter) params.set('filter', b64(filter))
      if (showClosed) params.set('status', 'closed')
      const qs = params.toString()
      return req('/tasks' + (qs ? `?${qs}` : ''))
    },
    get:    (id)     => req(`/tasks/${id}`),
    create: (text)   => req('/tasks', { method: 'POST', ...json({ text }) }),
    update: (id, text) => req(`/tasks/${id}`, { method: 'PATCH', ...json({ text }) }),
    close:  (id, text) => {
      const lines = (text ?? '').split('\n')
      let first = lines[0].replace(/\s*§\S+/g, '').trim() + ' §closed'
      if (!first.includes('>')) first += ' >web.taskmgt'
      const finalText = [first, ...lines.slice(1)].join('\n')
      return req(`/tasks/${id}`, { method: 'PATCH', ...json({ text: finalText }) })
    },
    delete: (id)     => req(`/tasks/${id}`, { method: 'DELETE' }),
  },
  filters: {
    list:    ()                   => req('/filters'),
    create:  (name, filter)       => req('/filters', { method: 'POST', ...json({ name, filter }) }),
    update:  (idx, name, filter)  => req(`/filters/${idx}`, { method: 'PATCH', ...json({ name, filter }) }),
    delete:  (idx)                => req(`/filters/${idx}`, { method: 'DELETE' }),
    reorder: (filters)            => req('/filters', { method: 'PUT', ...json(filters) }),
  },
  counts:    () => req('/counts'),
  tags:      () => req('/tags'),
  locations: () => req('/locations'),
}

export function viewToFilter(view, tag, location) {
  switch (view) {
    case 'inbox':    return '^inbox'
    case 'today':    return '^today'
    case 'overdue':  return '^overdue'
    case 'closed':   return '§closed'
    case 'tag':      return tag      ? `#${tag}`       : ''
    case 'location': return location ? `@${location}`  : ''
    case 'wait':     return '§wait'
    case 'started':  return '§started'
    default:         return ''
  }
}

export function stripTokens(text) {
  const firstLine = (text ?? '').split('\n')[0]
  return firstLine.replace(/\s*([!#@^=§>][^\s]+|\+\+?[^\s]+|<[^\s]+)/g, '').trim()
}

// Lines after the first that start with "* " are annotation/note lines.
// The literal "\n" sequence in a note is unescaped to a real newline.
export function annotations(text) {
  return (text ?? '').split('\n').slice(1)
    .filter(line => line.startsWith('* '))
    .map(line => line.slice(2).replace(/\\n/g, '\n'))
}
