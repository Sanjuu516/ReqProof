import {
  User,
  Project,
  Artifact,
  Requirement,
  AtomicClaim,
  RequirementGraph,
  AnalysisRun,
  ClaimResult,
  EvidenceRecord
} from '../types';

const API_BASE = '/api';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('reqproof_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errData = await response.json();
      if (errData.detail) errorMsg = errData.detail;
    } catch (_) {}
    throw new Error(errorMsg);
  }

  return response.json();
}

export const api = {
  // Auth
  async register(data: { name: string; email: string; password: string }) {
    return request<{ access_token: string; token_type: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async login(data: { email: string; password: string }) {
    return request<{ access_token: string; token_type: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  // Projects
  async listProjects(): Promise<Project[]> {
    return request<Project[]>('/projects');
  },

  async getProject(projectId: number): Promise<Project> {
    return request<Project>(`/projects/${projectId}`);
  },

  async createProject(data: { project_name: string; description?: string; source_version?: string }): Promise<Project> {
    return request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async deleteProject(projectId: number): Promise<{ message: string }> {
    return request<{ message: string }>(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  },

  async uploadProjectZip(projectId: number, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('reqproof_token');

    const res = await fetch(`${API_BASE}/projects/${projectId}/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload project ZIP archive');
    }
    return res.json();
  },

  async listArtifacts(projectId: number): Promise<Artifact[]> {
    return request<Artifact[]>(`/projects/${projectId}/artifacts`);
  },

  async getProjectHistory(projectId: number): Promise<AnalysisRun[]> {
    return request<AnalysisRun[]>(`/projects/${projectId}/history`);
  },

  // Requirements & Claims
  async createRequirement(projectId: number, data: { requirement_text: string }): Promise<Requirement> {
    return request<Requirement>(`/projects/${projectId}/requirements`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async listRequirements(projectId: number): Promise<Requirement[]> {
    return request<Requirement[]>(`/projects/${projectId}/requirements`);
  },

  async triggerDecomposition(requirementId: number): Promise<AtomicClaim[]> {
    return request<AtomicClaim[]>(`/requirements/${requirementId}/decompose`, {
      method: 'POST',
    });
  },

  async updateClaim(claimId: number, data: Partial<AtomicClaim>): Promise<AtomicClaim> {
    return request<AtomicClaim>(`/claims/${claimId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async getRequirementGraph(projectId: number): Promise<RequirementGraph> {
    return request<RequirementGraph>(`/projects/${projectId}/graph`);
  },

  // Analysis & Verification Runs
  async triggerAnalysisRun(projectId: number): Promise<AnalysisRun> {
    return request<AnalysisRun>(`/projects/${projectId}/analysis-runs`, {
      method: 'POST',
    });
  },

  async getAnalysisRun(runId: number): Promise<AnalysisRun> {
    return request<AnalysisRun>(`/analysis-runs/${runId}`);
  },

  async getAnalysisResults(runId: number): Promise<ClaimResult[]> {
    return request<ClaimResult[]>(`/analysis-runs/${runId}/results`);
  },

  async getClaimEvidence(claimId: number): Promise<EvidenceRecord[]> {
    return request<EvidenceRecord[]>(`/claims/${claimId}/evidence`);
  },

  // Reports
  getReportDownloadUrl(runId: number, format: 'pdf' | 'csv' = 'pdf'): string {
    const token = localStorage.getItem('reqproof_token');
    return `${API_BASE}/reports/${runId}/download?format=${format}`;
  },
};
