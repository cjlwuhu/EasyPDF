export type ParagraphStatus = "pending" | "translating" | "translated" | "failed" | "corrected";

export interface DocumentSummary {
  id: number;
  title: string;
  original_filename: string;
  status: string;
}

export interface Paragraph {
  id: number;
  page_number: number;
  order_index: number;
  source_text: string;
  translated_text: string;
  status: ParagraphStatus;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface DocumentDetail extends DocumentSummary {
  paragraphs: Paragraph[];
}

export interface TranslationJob {
  job_id: number;
  document_id: number;
  status: string;
  total_count: number;
  completed_count: number;
  failed_count: number;
}

export interface GlossaryTerm {
  id: number;
  source_term: string;
  target_term: string;
  note: string;
  enabled: boolean;
  keep_english: boolean;
}
