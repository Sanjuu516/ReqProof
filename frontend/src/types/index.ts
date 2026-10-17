export type VerificationStatus =
  | 'Fully Satisfied'
  | 'Partially Satisfied'
  | 'Missing'
  | 'Contradictory'
  | 'Unverifiable';

export interface User {
  user_id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
}

export interface Project {
  project_id: number;
  user_id: number;
  project_name: string;
  description?: string;
  source_version?: string;
  created_at: string;
  artifacts_count: number;
  requirements_count: number;
}

export interface Artifact {
  artifact_id: number;
  project_id: number;
  artifact_path: string;
  artifact_type: 'source' | 'ui' | 'api' | 'test' | 'test_report' | 'config' | 'other';
  language?: string;
  content_hash?: string;
  analysis_status: string;
}

export interface AtomicClaim {
  claim_id: number;
  requirement_id: number;
  claim_text: string;
  expected_behavior?: string;
  verification_criteria?: string;
  relevant_artifact_types: string;
  review_status: string;
  created_at: string;
}

export interface Requirement {
  requirement_id: number;
  project_id: number;
  requirement_text: string;
  created_at: string;
  updated_at: string;
  claims: AtomicClaim[];
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  data: Record<string, any>;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
}

export interface RequirementGraph {
  project_id: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface EvidenceRecord {
  evidence_id: number;
  analysis_run_id: number;
  claim_id: number;
  artifact_id?: number;
  evidence_type: 'static' | 'ui' | 'api' | 'runtime' | 'test';
  polarity: 'supporting' | 'contradicting' | 'inconclusive';
  observation: string;
  location_reference?: string;
  provenance?: string;
  created_at: string;
}

export interface ClaimResult {
  result_id: number;
  analysis_run_id: number;
  claim_id: number;
  claim_text?: string;
  status: VerificationStatus;
  reason_codes?: string;
  explanation: string;
  sufficiency_state: 'sufficient' | 'insufficient';
  evidence_records: EvidenceRecord[];
  created_at: string;
}

export interface AnalysisRun {
  analysis_run_id: number;
  project_id: number;
  source_version?: string;
  status: string;
  started_at: string;
  completed_at?: string;
  total_claims: number;
  fully_satisfied: number;
  partially_satisfied: number;
  missing: number;
  contradictory: number;
  unverifiable: number;
}
