/**
 * TypeScript型定義
 * 星の羅針盤「あとらす」フロントエンド
 */

/** 出生情報 */
export interface Birth {
  date: string;
  time?: string;
  place?: string;
}

/** フォームデータ（ユーザー入力情報） */
export interface FormData {
  name?: string;
  gender?: string;
  birth?: Birth;
  concerns?: string[];
  problem?: string;
  wrist_inner_cm?: number;
  bead_size_mm?: number;
  bracelet_type?: string;
  stone_method?: string;
  stone_option?: string;
  today_comment?: string;
  line_user_id?: string;
  design_style?: string;
}

/** オラクルカード */
export interface OracleCard {
  name: string;
  image_url: string;
  is_upright: boolean;
  meaning: string;
}

/** 石情報 */
export interface Stone {
  name: string;
  reason: string;
  count?: number;
  position?: string;
}

/** 商品情報 */
export interface Product {
  id?: number;
  slug?: string;
  label?: string;
  name?: string;
  price?: number;
}

/** 診断結果 */
export interface DivinationResult {
  diagnosis_id?: string;
  stone_name?: string;
  product_slug?: string;
  destiny_map?: string;
  past?: string;
  present_future?: string;
  element_diagnosis?: string;
  oracle_message?: string;
  bracelet_proposal?: string;
  stone_support_message?: string;
  oracle_card?: OracleCard;
  stones_for_user?: Stone[];
  products?: Product[];
  image_url?: string;
  product_name?: string;
  short_message?: string;
  oraclecardname?: string;
  id?: number;
  bracelet_name?: string;
  bracelet_name_en?: string;
  name_en?: string;
  image?: string;
  design_text?: string;
  stone_counts?: Record<string, number>;
  bracelet?: { product_slug?: string };
  [key: string]: unknown;
}

/** ブレスレット生成結果 */
export interface BraceletResult {
  product_slug?: string;
  stone_name?: string;
  design_text?: string;
  image_url?: string;
  product_name?: string;
  bracelet_name?: string;
  name?: string;
  name_en?: string;
  bracelet_name_en?: string;
  image?: string;
  stone_counts?: Record<string, number>;
}

/** LIFF SDK型宣言 */
declare global {
  const liff: {
    init(config: { liffId: string }): Promise<void>;
    isLoggedIn(): boolean;
    getProfile(): Promise<{ userId: string; displayName: string }>;
    openWindow(params: { url: string; external?: boolean }): void;
  };

  interface Window {
    LINE_USER_ID?: string;
    diagnosisId?: string;
    // HTMLのonclickから呼び出す関数群
    selectMode: (mode: string) => void;
    nextStep: () => void;
    executeDiagnose: () => void;
    selectGender: (gender: string, el: HTMLElement) => void;
    toggleConcern: (el: HTMLElement, concern: string) => void;
    selectStoneMethod: (method: string, el: HTMLElement) => void;
    showStoneOptions: () => void;
    selectStoneOption: (option: string, el: HTMLElement) => void;
    confirmStoneSelection: () => void;
    showProductCandidates: () => void;
    selectProductCandidate: (index: number, el: HTMLElement) => void;
    goToSelectedProduct: () => void;
    goLineRegister: () => void;
    selectOrderType: (type: string) => void;
    selectWristSize: (size: number, el: HTMLElement) => void;
    selectBraceletType: (type: string, el: HTMLElement) => void;
    selectDesign: (style: string, el: HTMLElement) => void;
    buildBracelet: () => void;
    goToProduct: () => void;
    confirmOrder: () => void;
    restartFromBeginning: () => void;
    showNextSection: () => void;
    submitTodayComment: () => void;
    showNextSection: () => void;
  }

  /** flatpickr */
  function flatpickr(selector: string, options: Record<string, unknown>): void;
}
