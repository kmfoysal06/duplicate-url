export interface CrawledPage {
  original_url: string;
  final_url: string;
  status_code: number | null;
  title: string;
  meta_description: string;
  canonical_url: string | null;
  h1: string[];
  h2: string[];
  main_text: string;
  word_count: number;
  content_hash: string | null;
  error: string | null;
}

export interface EvaluatedPair {
  pair_id: string;
  url1: string;
  url2: string;
  similarity_score: number;
  classification: string;
  title1: string;
  title2: string;
  title_similarity: number;
  title_match: boolean;
  h1_1: string[];
  h1_2: string[];
  h1_similarity: number;
  h1_match: boolean;
  h2_1: string[];
  h2_2: string[];
  h2_similarity: number;
  canonical1: string | null;
  canonical2: string | null;
  same_canonical: boolean;
  canonical_status: string;
  status_code1: number | null;
  status_code2: number | null;
  word_count1: number;
  word_count2: number;
  recommended_action: string;
}

export interface DuplicateCluster {
  cluster_id: string;
  highest_classification: string;
  highest_similarity: number;
  member_count: number;
  members: string[];
  pairs_count: number;
}

export interface AnalysisSummary {
  total_urls_submitted: number;
  successfully_crawled: number;
  failed_urls: number;
  exact_duplicate_groups: number;
  near_duplicate_groups: number;
  potential_duplicate_groups: number;
  pages_sharing_canonicals: number;
  total_duplicate_pairs: number;
  evaluated_pairs_count: number;
}

export interface JobProgress {
  stage: string;
  current: number;
  total: number;
  percent: number;
  current_url: string;
  message: string;
}

export interface ConsolidationAction {
  source_url: string;
  cluster_id: string;
  action: '301_REDIRECT' | 'MERGE_AND_REDIRECT' | 'CANONICALIZE' | 'PRUNE_OR_DELETE' | 'DIFFERENTIATE' | 'KEEP_PRIMARY';
  action_label: string;
  target_url: string | null;
  status_code: number | null;
  word_count: number;
  priority: 'High' | 'Medium' | 'Low';
  reason: string;
  details?: {
    winner_reasons?: string[];
    authority_score?: number;
    why_target?: string;
    redirect_type?: string;
    merge_guidance?: string;
    target_recommendation?: string;
    canonical_target?: string;
    advice?: string;
  };
}

export interface ConsolidationPlan {
  summary: {
    total_actions_recommended: number;
    to_redirect_301: number;
    to_merge_and_redirect: number;
    to_prune_or_delete: number;
    to_canonicalize: number;
    to_differentiate: number;
    primary_master_pages: number;
  };
  actions: ConsolidationAction[];
  export_snippets: {
    nginx: string;
    apache: string;
    cloudflare_csv: string;
  };
}

export interface TopicClusterPage {
  url: string;
  role: 'PRIMARY' | 'SECONDARY';
  action: 'KEEP_PRIMARY' | '301_REDIRECT' | 'MERGE_CONTENT' | 'DELETE_OR_PRUNE' | 'KEEP_SEPARATE' | 'IMPROVE_CONTENT';
  action_label: string;
  target_url: string | null;
  title: string;
  search_intent: string;
  topic_source?: 'USER_DEFINED' | 'AUTO_DETECTED';
  topic_confidence?: number;
  matched_topic?: string;
  status_code: number | null;
  word_count: number;
  similarity_to_primary?: number;
  priority: 'High' | 'Medium' | 'Low';
  reason: string;
  action_summary: string;
}

export interface TopicCluster {
  cluster_id: string;
  topic: string;
  topic_source?: 'USER_DEFINED' | 'AUTO_DETECTED';
  member_count: number;
  primary_url: string;
  search_intents: Record<string, number>;
  has_intent_conflict: boolean;
  pages: TopicClusterPage[];
}

export interface TopicClustersResult {
  summary: {
    total_topic_clusters: number;
    total_pages_analyzed: number;
    total_primary_master_urls: number;
    total_recommended_redirects: number;
    total_recommended_merges: number;
    total_recommended_pruning: number;
    total_keep_separate: number;
    total_improve_content: number;
  };
  clusters: TopicCluster[];
}

export interface AnalysisResult {
  summary: AnalysisSummary;
  clusters: DuplicateCluster[];
  pairs: EvaluatedPair[];
  pages: CrawledPage[];
  consolidation_plan?: ConsolidationPlan;
  topic_clusters?: TopicClustersResult;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'pending' | 'crawling' | 'analyzing' | 'completed' | 'failed';
  progress: JobProgress;
  results: AnalysisResult | null;
  error: string | null;
}

export interface DiffToken {
  text: string;
  type: 'same' | 'added' | 'removed';
}

export interface DetailedPairDiff {
  pair_id: string;
  url1: string;
  url2: string;
  final_url1: string;
  final_url2: string;
  similarity_score: number;
  classification: string;
  recommended_action: string;
  title1: string;
  title2: string;
  title_match: boolean;
  meta_desc1: string;
  meta_desc2: string;
  h1_1: string[];
  h1_2: string[];
  h1_match: boolean;
  h2_1: string[];
  h2_2: string[];
  canonical1: string | null;
  canonical2: string | null;
  same_canonical: boolean;
  canonical_status: string;
  status_code1: number | null;
  status_code2: number | null;
  word_count1: number;
  word_count2: number;
  shared_content: string[];
  unique_to_page1: string[];
  unique_to_page2: string[];
  diff_tokens_p1: DiffToken[];
  diff_tokens_p2: DiffToken[];
}
