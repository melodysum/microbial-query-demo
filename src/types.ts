export type Filter = { feature: string; operator: string; value: string | number; unit?: string }
export type Feature = { key: string; label: string; type: string; unit: string; options: string[]; description?: string }
export type Strain = {
  id: string
  accession: string
  species: string
  strain_name: string
  type_strain: string
  internal_id: string
  genome_path: string
  lineage_json: string
  match_reasons?: { feature: string; label: string; status: string; observed?: string }[]
  missing_features?: string[]
}
export type SearchResponse = { confirmed: Strain[]; possible: Strain[]; counts: { confirmed: number; possible: number } }
export type Taxon = { name: string; rank?: string; count: number; children: Taxon[] }
export type Observation = { id: number; feature: string; value: string; unit: string; condition_text: string; evidence_status: string; evidence?: { title: string; excerpt: string } }
export type Literature = { id: string; record_type: string; original_number?: number; title: string; authors?: string; journal?: string; year: number; shared_date?: string; project_relation: string; verification_status: string; related_strains: string[] }
export type SequenceMatch = { strain: Strain; method: string; ani?: number; score: number; score_type: string; aligned_fraction_ref?: number; aligned_fraction_query?: number }
export type Health = { status: string; version: string; strains: number; species: number; features: number; literature: number; sequence_engine: string; qwen_enabled: boolean; phenotype_notice: string }
