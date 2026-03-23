/**
 * グローバル状態管理
 * アプリケーション全体で共有される状態を一元管理する
 */

import type { FormData, DivinationResult, Product } from './types';

export const state = {
  /** 現在のUIステート */
  userState: 'mode_select' as string,
  /** ユーザー入力データ */
  formData: {} as FormData,
  /** 選択中のモード */
  selectedMode: null as string | null,
  /** メッセージ表示キュー */
  messageQueue: Promise.resolve(),
  /** 診断結果 */
  divinationResult: null as DivinationResult | null,
  /** 商品候補リスト */
  productCandidates: [] as Product[],
  /** 選択中の商品インデックス */
  selectedProductIndex: null as number | null,
  /** ユーザーID */
  userId: null as string | null,
  /** ローディングメッセージのインデックス */
  thinkingIndex: 0,
};

export const API_BASE = '/api';
