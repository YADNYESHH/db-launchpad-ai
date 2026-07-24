import type {
  AuditEvent,
  DiscoveryResponse,
  PortfolioSummary,
  ProfileBundle,
  RecommendationRecord,
  ScoreRecord,
  UserPublic,
  WeightConfig,
} from './types'

const TOKEN_KEY = 'launchpad_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { ...(init.headers as Record<string, string>) }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (init.body && !(init.body instanceof URLSearchParams)) headers['Content-Type'] = 'application/json'

  const resp = await fetch(path, { ...init, headers })
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail ?? detail
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(resp.status, detail)
  }
  if (resp.status === 204) return undefined as T
  return resp.json() as Promise<T>
}

export async function login(email: string, password: string): Promise<{ access_token: string; user: UserPublic }> {
  const body = new URLSearchParams({ username: email, password })
  return request('/auth/login', { method: 'POST', body })
}

export async function me(): Promise<UserPublic> {
  return request('/auth/me')
}

export async function listProfiles(): Promise<ProfileBundle[]> {
  return request('/profiles')
}

export async function getProfile(startupId: string): Promise<ProfileBundle> {
  return request(`/profiles/${startupId}`)
}

export async function scoreProfile(startupId: string): Promise<{ score_id: string; score_record: ScoreRecord }> {
  return request(`/profiles/${startupId}/score`, { method: 'POST' })
}

export async function generateRecommendation(
  startupId: string,
  force = false,
): Promise<RecommendationRecord> {
  return request('/recommendations/generate', {
    method: 'POST',
    body: JSON.stringify({ startup_id: startupId, force }),
  })
}

export async function decideRecommendation(
  recommendationId: string,
  decision: 'approved' | 'revised' | 'rejected',
): Promise<RecommendationRecord> {
  return request(`/recommendations/${recommendationId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  })
}

export async function getAuditTrail(startupId: string): Promise<AuditEvent[]> {
  return request(`/audit/${startupId}`)
}

export async function getActiveWeights(): Promise<WeightConfig> {
  return request('/weights')
}

export async function discoverStartups(sector: string, limit = 4): Promise<DiscoveryResponse> {
  return request('/discovery/search', {
    method: 'POST',
    body: JSON.stringify({ sector, limit }),
  })
}

export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  return request('/portfolio/summary')
}

export async function listAllWeights(): Promise<WeightConfig[]> {
  return request('/weights/all')
}

export async function proposeWeights(body: {
  change_reason: string
  sub_score_driver_tables?: Record<string, unknown> | null
  final_rollup_weights?: Record<string, number> | null
}): Promise<WeightConfig> {
  return request('/weights/propose', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function activateWeights(versionId: string): Promise<WeightConfig> {
  return request(`/weights/${versionId}/activate`, { method: 'POST' })
}

export { ApiError }
