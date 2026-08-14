import type { CopilotResponse, ImportJob, Metrics, Session } from './types'

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers ?? {}),
    },
  })

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const body = await response.json()
      message = body.detail ?? body.file?.[0] ?? JSON.stringify(body)
    } catch {
      const body = await response.text()
      if (body) message = body
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function createSession(visitorId: string) {
  return request<Session>('/api/sessions/', {
    method: 'POST',
    body: JSON.stringify({ visitor_id: visitorId }),
  })
}

export function getSession(visitorId: string) {
  return request<Session>(`/api/sessions/${visitorId}/`)
}

export function updateProfile(visitorId: string, companyName: string, businessType: string) {
  return request<Session>(`/api/sessions/${visitorId}/profile/`, {
    method: 'PATCH',
    body: JSON.stringify({ company_name: companyName, business_type: businessType }),
  })
}

export async function connectIntegration(visitorId: string, provider: string) {
  const result = await request<{ session: Session }>(`/api/sessions/${visitorId}/integration/`, {
    method: 'POST',
    body: JSON.stringify({ provider, external_store_id: `demo-${provider}` }),
  })
  return result.session
}

export async function createCampaign(visitorId: string, name: string, channel = 'email') {
  const result = await request<{ session: Session }>(`/api/sessions/${visitorId}/campaigns/`, {
    method: 'POST',
    body: JSON.stringify({ name, channel }),
  })
  return result.session
}

export function uploadCustomerCsv(visitorId: string, file: File) {
  const form = new FormData()
  form.append('file', file)
  return request<ImportJob>(`/api/sessions/${visitorId}/imports/`, {
    method: 'POST',
    body: form,
  })
}

export function getImportStatus(visitorId: string, importId: number) {
  return request<ImportJob>(`/api/sessions/${visitorId}/imports/${importId}/`)
}

export function getMetrics() {
  return request<Metrics>('/api/metrics/')
}

export function getCopilot(visitorId: string, goal: string) {
  return request<CopilotResponse>(`/api/sessions/${visitorId}/copilot/`, {
    method: 'POST',
    body: JSON.stringify({ goal }),
  })
}
