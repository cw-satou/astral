/**
 * 商品選択モジュール
 */

import { state } from './state';
import { addMsg, setInputArea } from './chat';
import { getUserNameForDisplay } from './profile';

/** 商品候補を表示 */
export function showProductCandidates(): void {
  if (!state.productCandidates || state.productCandidates.length === 0) {
    addMsg('関連するブレスレット候補が見つかりませんでした。', false);
    return;
  }

  if (state.selectedProductIndex === null && state.productCandidates.length > 0) {
    state.selectedProductIndex = 0;
  }

  const nameForDisplay = getUserNameForDisplay();

  let html = `
    <div class="result-section">
      <h3>💎 ${nameForDisplay}におすすめのブレスレット候補</h3>
      <p style="font-size:13px;margin:4px 0 10px;">
        今回の診断結果から導かれたブレスレット候補です。<br>
        気になるものを1本選んで、詳しいページを開いてください。
      </p>
  `;

  state.productCandidates.forEach((p, idx) => {
    const isSelected = idx === state.selectedProductIndex;
    const label = p.label || p.name || p.slug || `候補${idx + 1}`;
    const priceText = p.price ? `（${p.price}円）` : '';
    html += `
      <button
        class="btn-toggle ${isSelected ? 'active' : ''}"
        style="display:block;width:100%;text-align:left;margin:4px 0;"
        onclick="selectProductCandidate(${idx}, this)"
      >
        ${idx + 1}. ${label} ${priceText}
      </button>
    `;
  });

  html += `</div>
    <button class="btn" onclick="goToSelectedProduct()">🛒 選んだブレスレットのページを開く</button>
    <button class="btn btn-secondary" onclick="restartFromBeginning()">🔄 もう一度占う</button>
  `;

  setInputArea(html);
}

/** 商品候補を選択 */
export function selectProductCandidate(index: number, el: HTMLElement): void {
  state.selectedProductIndex = index;
  const container = el.parentElement;
  container?.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** 選択した商品ページへ遷移 */
export function goToSelectedProduct(): void {
  if (
    !state.productCandidates ||
    state.productCandidates.length === 0 ||
    state.selectedProductIndex === null
  ) {
    addMsg('先に、見てみたいブレスレットを1本選んでください。', false);
    return;
  }

  const p = state.productCandidates[state.selectedProductIndex];

  if (p.id) {
    const diagnosisId = window.diagnosisId;
    let url = `https://spicastar.info/atlas/?p=${p.id}`;
    if (diagnosisId) {
      url += `&d=${diagnosisId}`;
    }
    window.location.href = url;
  } else {
    addMsg('商品ページの情報が足りませんでした。', false);
  }
}

/** LINE登録ページへ遷移 */
export function goLineRegister(): void {
  const diagnosisId = window.diagnosisId;
  const selected = state.productCandidates[state.selectedProductIndex ?? 0] || null;

  const lines = [
    '診断結果をLINEでも受け取りたいです。',
    diagnosisId ? `診断ID: ${diagnosisId}` : '',
    selected && selected.id ? `商品ID: ${selected.id}` : '',
  ].filter(Boolean);

  const text = encodeURIComponent(lines.join('\n'));
  window.location.href = `https://line.me/R/oaMessage/@586spjck/?${text}`;
}
