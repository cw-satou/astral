/**
 * ブレスレット関連モジュール
 * サイズ選択、ブレスレット生成、結果表示
 */

import { state } from './state';
import { addMsg, setInputArea, clearInputArea, setProgress, formatText, scrollChatToBottom } from './chat';
import { getUserNameForDisplay, saveProfileToLocalStorage } from './profile';

/** ブレスレットサイズ選択ステップ */
export async function stepBraceletSize(): Promise<void> {
  const nameForDisplay = getUserNameForDisplay();
  await addMsg('次はブレスレットのサイズを決めます。', false);
  await addMsg('ふだん身につけることをイメージしながら選んでみてください。', false);
  await addMsg('手首の内径に近いサイズを選ぶと自然に着けられます。', false);
  await addMsg('あとからサイズ直しをしなくて済むように、ここだけ少し丁寧に選びましょう。', false);

  const savedWrist = state.formData.wrist_inner_cm || 16.0;
  const savedType = state.formData.bracelet_type || 'birth_top_element_side';

  setInputArea(`
    <div class="input-field">
      <label>手首の内径（cm）</label>
      <div class="btn-group">
        <button class="btn-toggle ${savedWrist === 16 ? 'active' : ''}" onclick="selectWristSize(16, this)">16cm</button>
        <button class="btn-toggle ${savedWrist === 18 ? 'active' : ''}" onclick="selectWristSize(18, this)">18cm</button>
        <button class="btn-toggle ${savedWrist === 20 ? 'active' : ''}" onclick="selectWristSize(20, this)">20cm</button>
      </div>
    </div>
    <div class="input-field">
      <label>ブレスレットのタイプ</label>
      <div class="btn-group">
        <button class="btn-toggle ${savedType === 'birth_top_element_side' ? 'active' : ''}" onclick="selectBraceletType('birth_top_element_side', this)">誕生石をトップ、エレメントの石をサイドに</button>
        <button class="btn-toggle ${savedType === 'element_top_only' ? 'active' : ''}" onclick="selectBraceletType('element_top_only', this)">エレメントの石だけをトップに</button>
      </div>
    </div>
    <button class="btn" onclick="buildBracelet()">💎 この石で作られたブレスレットを見る</button>
  `);
}

/** 手首サイズ選択 */
export function selectWristSize(size: number, el: HTMLElement): void {
  state.formData.wrist_inner_cm = size;
  el.parentElement?.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** ブレスレットタイプ選択 */
export function selectBraceletType(type: string, el: HTMLElement): void {
  state.formData.bracelet_type = type;
  el.parentElement?.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** デザインスタイル選択 */
export function selectDesign(style: string, el: HTMLElement): void {
  state.formData.design_style = style;
  document.querySelectorAll('.input-field:last-child .btn-group .btn-toggle')
    .forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** ブレスレット生成 */
export async function buildBracelet(): Promise<void> {
  addMsg('この石を中心に、あなたのブレスレットを形にします。', false);
  saveProfileToLocalStorage();

  setInputArea(`
    <div class="loading">
      <div class="spinner"></div>
      <p>ブレスレットを準備しています... 💎</p>
    </div>
  `);

  const result = state.divinationResult;
  const json = {
    product_slug: result?.product_slug,
    stone_name: result?.stone_name,
    design_text: result?.bracelet_proposal || '',
    image_url: result?.image_url,
    product_name: result?.product_name,
  };

  await addMsg('このブレスレットは、あなたの診断結果をもとに選ばれたものです。', false);
  await addMsg('今のあなたの流れに合う石を中心にした一本です。', false);
  displayBraceletResult(json);
}

/** ブレスレット結果を表示 */
function displayBraceletResult(data: Record<string, unknown>): void {
  setProgress(4, 4, 'ブレスレット生成');
  const nameForDisplay = getUserNameForDisplay();
  clearInputArea();

  const chatBox = document.getElementById('chatBox');
  if (!chatBox) return;

  const section = document.createElement('div');
  section.className = 'result-section';

  let html = `<h3>💎 ${nameForDisplay}を導くブレスレット</h3>`;
  html += `<p style="font-size:18px;font-weight:bold;">${data.product_name || data.bracelet_name || ''}</p>`;

  if (data.name || data.bracelet_name) {
    html += `<p style="font-weight:bold;font-size:16px;margin-top:6px;">${data.name || data.bracelet_name}</p>`;
  }
  if (data.name_en || data.bracelet_name_en) {
    html += `<p style="font-size:12px;opacity:0.7;">${data.name_en || data.bracelet_name_en}</p>`;
  }

  const img = (data.image_url || data.image) as string;
  if (img) {
    html += `<img src="${img}" style="width:100%;border-radius:12px;margin:12px 0;">`;
  }
  if (data.design_text) {
    html += `<p>${formatText(data.design_text as string)}</p>`;
  }
  if (data.stone_counts) {
    html += `<p style="margin-top:12px;font-size:13px;">`;
    for (const [stone, count] of Object.entries(data.stone_counts as Record<string, number>)) {
      html += `${stone} × ${count}<br>`;
    }
    html += `</p>`;
  }

  section.innerHTML = html;
  chatBox.appendChild(section);
  scrollChatToBottom();

  setInputArea(`
    <button class="btn" onclick="goToProduct()">🛒 このブレスレットを購入する</button>
    <button class="btn btn-secondary" onclick="restartFromBeginning()">🔄 もう一度占う</button>
  `);
}

/** 商品ページへ遷移 */
export function goToProduct(): void {
  const result = state.divinationResult;
  const slug = result?.product_slug || result?.bracelet?.product_slug;
  if (!slug) {
    addMsg('商品ページが見つかりませんでした', false);
    return;
  }
  const url = `https://spicastar.info/atlas/?p=` + result?.id;
  window.location.href = url;
}

/** 注文確認（LINEへ遷移） */
export function confirmOrder(): void {
  const diagnosisId = window.diagnosisId;
  const wrist = state.formData.wrist_inner_cm;
  const problem = state.formData.problem || '';
  const oracleCard = state.divinationResult?.oraclecardname || '';
  const lines = [
    'この内容でブレスレットを注文したいです。',
    diagnosisId ? `診断ID: ${diagnosisId}` : '',
    wrist ? `手首内径: ${wrist}cm` : '',
    problem ? `お悩み: ${problem}` : '',
    oracleCard ? `オラクルカード: ${oracleCard}` : '',
  ].filter(Boolean);
  const encoded = encodeURIComponent(lines.join('\n'));
  window.location.href = `https://line.me/R/oaMessage/@586spjck/?${encoded}`;
}
