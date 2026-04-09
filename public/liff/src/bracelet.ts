/**
 * ブレスレット関連モジュール
 * サイズ選択、ブレスレット生成、結果表示
 */

import { state } from './state';
import { addMsg, setInputArea, clearInputArea, setProgress, formatText, scrollChatToBottom } from './chat';
import { getUserNameForDisplay, saveProfileToLocalStorage } from './profile';
import { openUrl } from './liff';

/** ブレスレットサイズ選択ステップ */
export async function stepBraceletSize(): Promise<void> {
  const nameForDisplay = getUserNameForDisplay();
  await addMsg('次はブレスレットのサイズを決めます。', false);
  await addMsg('ふだん身につけることをイメージしながら選んでみてください。', false);
  await addMsg('手首の内径に近いサイズを選ぶと自然に着けられます。', false);
  await addMsg('あとからサイズ直しをしなくて済むように、ここだけ少し丁寧に選びましょう。', false);

  const savedWrist = state.formData.wrist_inner_cm || 15.0;
  const savedType = state.formData.bracelet_type || 'birth_top_element_side';
  const wristSizes = [14, 15, 16, 17, 18, 19, 20];
  const wristButtons = wristSizes.map(s =>
    `<button class="btn-toggle ${savedWrist === s ? 'active' : ''}" onclick="selectWristSize(${s}, this)">${s}cm</button>`
  ).join('');

  setInputArea(`
    <div class="input-field">
      <label>手首の内径（cm）</label>
      <div class="btn-group">${wristButtons}</div>
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

  // 使用する石を決定:
  //   診断経路 → productCandidates[0].stones（マッチングエンジンが選定した石）
  //   石好み経路 → divinationResult.stones_for_user（色・効果・星座で選んだ石）
  type RecType = { stones?: string[]; woo_product_id?: number };
  const topRec = (state.productCandidates as RecType[])[0];
  const stonesForUser: Array<{ name: string; reason: string; count: number }> =
    topRec?.stones?.map(name => ({ name, reason: '星読みによる選定', count: 1 }))
    ?? (result?.stones_for_user?.map(s => ({ name: s.name, reason: s.reason ?? '', count: s.count ?? 1 })) ?? []);
  const wooProductId = topRec?.woo_product_id ?? result?.id;

  // オーダー情報をサーバーに送信して記録
  let stoneCounts: Record<string, number> | undefined;
  try {
    const res = await fetch('/api/build-bracelet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        diagnosis_id:    window.diagnosisId,
        woo_product_id:  wooProductId,
        stones_for_user: stonesForUser,
        wrist_inner_cm:  state.formData.wrist_inner_cm,
        bead_size_mm:    state.formData.bead_size_mm || 8,
        bracelet_type:   state.formData.bracelet_type,
      }),
    });
    if (res.ok) {
      const apiData = await res.json();
      // APIレスポンスから stone_counts を取得
      const summary = apiData.order_summary as Record<string, unknown> | undefined;
      if (summary?.stone_counts) {
        stoneCounts = summary.stone_counts as Record<string, number>;
      } else if (Array.isArray(apiData.stones)) {
        stoneCounts = {};
        for (const s of apiData.stones as Array<{ name: string; count?: number }>) {
          stoneCounts[s.name] = s.count || 1;
        }
      }
    }
  } catch {
    /* サイレント失敗：表示は続行 */
  }

  await addMsg('このブレスレットは、あなたの診断結果をもとに選ばれたものです。', false);
  await addMsg('今のあなたの流れに合う石を中心にした一本です。', false);

  displayBraceletResult({
    product_slug: result?.product_slug,
    stone_name:   result?.stone_name,
    design_text:  result?.bracelet_proposal || '',
    image_url:    result?.image_url,
    product_name: result?.product_name,
    stone_counts: stoneCounts,
  });
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
  const productId = result?.id;
  const slug = result?.product_slug || result?.bracelet?.product_slug;

  if (!productId && !slug) {
    addMsg('商品ページが見つかりませんでした', false);
    return;
  }

  const base = productId
    ? `https://spicastar.info/atlas/?p=${productId}`
    : `https://spicastar.info/atlas/shop/${slug}/`;

  const diagnosisId = window.diagnosisId;
  const url = diagnosisId
    ? `${base}${base.includes('?') ? '&' : '?'}d=${diagnosisId}`
    : base;

  openUrl(url);
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
  window.location.href = `https://line.me/R/oaMessage/@586spjck/?text=${encoded}`;
}
