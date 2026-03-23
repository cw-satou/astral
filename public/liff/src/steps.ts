/**
 * フロー制御モジュール
 * 各ステップの遷移とフォーム表示
 */

import { state } from './state';
import { addMsg, setInputArea, clearInputArea, setProgress } from './chat';
import { getUserNameForDisplay, saveProfileToLocalStorage, getGreetingMessage, loadProfileFromLocalStorage } from './profile';
import { stepTodayFortune, runTodayFortune } from './fortune';
import { stepBraceletSize } from './bracelet';

/** モード選択画面 */
export function stepModeSelect(): void {
  state.userState = 'mode_select';
  addMsg('今日はどちらにしますか？', false);
  setInputArea(`
    <button class="btn" onclick="selectMode('divination')">✨ 導きの石を診断する</button>
    <button class="btn" onclick="selectMode('today_fortune')">🔮 今日の運勢を診断する</button>
    <button class="btn btn-secondary" onclick="selectMode('stone_select')">💎 好みでブレスレットを選ぶ</button>
  `);
}

/** モードを選択 */
export function selectMode(mode: string): void {
  state.selectedMode = mode;
  if (mode === 'today_fortune') {
    addMsg('今日の運勢を診断する', true);
    stepTodayFortune().then(() => showAstrologicalInfoForm());
  } else if (mode === 'divination') {
    addMsg('導きの石を診断する', true);
    showAstrologicalInfoForm();
  } else {
    addMsg('好みでブレスレットを選ぶ', true);
    stepStoneSelectMethod();
  }
}

/** 占星術情報入力フォーム表示 */
export function showAstrologicalInfoForm(): void {
  setProgress(1, 4, 'プロフィール入力');
  addMsg('今のあなたについて少しだけ教えてください。\nはじめに、診断に必要な情報をお聞かせください。', false);

  const gender = state.formData.gender || '';
  const birth = state.formData.birth || {};
  const savedDate = birth.date || '';
  const savedTime = birth.time || '';
  const savedPlace = birth.place || '';
  const savedName = state.formData.name || '';

  state.userState = 'astrological_info';

  setInputArea(`
    <div class="input-field">
      <label>お名前（ニックネーム）</label>
      <input type="text" id="userName" value="${savedName}" placeholder="例：さと">
    </div>
    <div class="input-field">
      <label>性別 *</label>
      <div class="btn-group">
        <button class="btn-toggle ${gender === '女性' ? 'active' : ''}" onclick="selectGender('女性', this)">女性</button>
        <button class="btn-toggle ${gender === '男性' ? 'active' : ''}" onclick="selectGender('男性', this)">男性</button>
        <button class="btn-toggle ${gender === 'その他' ? 'active' : ''}" onclick="selectGender('その他', this)">その他</button>
      </div>
    </div>
    <div class="input-field">
      <label>生年月日 *</label>
      <input type="text" id="birthDate" value="${savedDate}" required>
    </div>
    <div class="input-field">
      <label>出生時間</label>
      <input type="text" id="birthTime" value="${savedTime}">
    </div>
    <div class="input-field">
      <label>出生地</label>
      <input type="text" id="birthPlace" placeholder="例：札幌市" value="${savedPlace}">
    </div>
    <button class="btn" onclick="nextStep()">次へ</button>
  `);

  flatpickr('#birthDate', { locale: 'ja', dateFormat: 'Y-m-d', maxDate: 'today' });
  flatpickr('#birthTime', { enableTime: true, noCalendar: true, dateFormat: 'H:i', time_24hr: true });
}

/** 性別選択 */
export function selectGender(gender: string, el: HTMLElement): void {
  state.formData.gender = gender;
  el.parentElement?.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** 次のステップへ進む */
export function nextStep(): void {
  if (state.userState === 'astrological_info') {
    const name = (document.getElementById('userName') as HTMLInputElement)?.value || '';
    const date = (document.getElementById('birthDate') as HTMLInputElement)?.value;
    const time = (document.getElementById('birthTime') as HTMLInputElement)?.value || '';
    const place = (document.getElementById('birthPlace') as HTMLInputElement)?.value || '';

    if (!state.formData.gender) {
      addMsg('性別を選んでください', false);
      return;
    }
    if (!date) {
      addMsg('生年月日は必須です', false);
      return;
    }

    state.formData.birth = { date, time, place };
    state.formData.name = name;
    saveProfileToLocalStorage();
    clearInputArea();

    if (state.selectedMode === 'today_fortune') {
      runTodayFortune();
    } else {
      stepConcerns();
    }
    return;
  } else if (state.userState === 'concerns') {
    stepProblem();
  }
}

/** 悩みテーマ選択 */
export function stepConcerns(): void {
  setProgress(2, 4, '悩みの診断');
  const nameForDisplay = getUserNameForDisplay();
  const text = [
    `${nameForDisplay}がいま、特に気になっているテーマを教えてください。`,
    '複数選んでも大丈夫です。',
  ].join('\n\n');

  addMsg(text, false);
  state.userState = 'concerns';

  setInputArea(`
    <div class="btn-group">
      <button class="btn-toggle" onclick="toggleConcern(this, '恋愛')">💕 恋愛</button>
      <button class="btn-toggle" onclick="toggleConcern(this, '仕事')">💼 仕事</button>
      <button class="btn-toggle" onclick="toggleConcern(this, '金運')">💰 金運</button>
      <button class="btn-toggle" onclick="toggleConcern(this, '健康')">🌿 健康</button>
      <button class="btn-toggle" onclick="toggleConcern(this, '人間関係')">🤝 人間関係</button>
      <button class="btn-toggle" onclick="toggleConcern(this, 'その他')">✨ その他</button>
    </div>
    <button class="btn" onclick="nextStep()">次へ</button>
  `);
}

/** 悩みトグル */
export function toggleConcern(el: HTMLElement, concern: string): void {
  state.formData.concerns = state.formData.concerns || [];
  if (el.classList.contains('active')) {
    el.classList.remove('active');
    state.formData.concerns = state.formData.concerns.filter(c => c !== concern);
  } else {
    el.classList.add('active');
    if (!state.formData.concerns.includes(concern)) {
      state.formData.concerns.push(concern);
    }
  }
}

/** 具体的な悩み入力 */
async function stepProblem(): Promise<void> {
  if (!state.formData.concerns || state.formData.concerns.length === 0) {
    addMsg('少なくとも1つ選んでください。', false);
    return;
  }
  addMsg(state.formData.concerns.join('、'), true);
  await addMsg(
    '具体的な状況やお気持ちを、書ける範囲で教えてください。\nうまくまとまっていなくても大丈夫です。',
    false
  );
  state.userState = 'problem';
  setInputArea(`
    <div class="input-field">
      <textarea id="problemText" placeholder="例：最近彼との関係がうまくいかなくて..."></textarea>
    </div>
    <button class="btn" onclick="executeDiagnose()">診断開始</button>
  `);
}

/** 石の選び方フロー */
function stepStoneSelectMethod(): void {
  addMsg('どの方法で石を選びますか？', false);
  setInputArea(`
    <div class="btn-group">
      <button class="btn-toggle active" onclick="selectStoneMethod('color', this)">色</button>
      <button class="btn-toggle" onclick="selectStoneMethod('effect', this)">効果</button>
      <button class="btn-toggle" onclick="selectStoneMethod('zodiac', this)">星座</button>
      <button class="btn-toggle" onclick="selectStoneMethod('moon', this)">月</button>
    </div>
    <button class="btn" onclick="showStoneOptions()">次へ</button>
  `);
}

/** 石の選び方を選択 */
export function selectStoneMethod(method: string, el: HTMLElement): void {
  state.formData.stone_method = method;
  el.parentElement?.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** 石のオプション表示 */
export function showStoneOptions(): void {
  const method = state.formData.stone_method || 'color';
  const methodLabelMap: Record<string, string> = {
    color: '色', effect: '効果', zodiac: '星座', moon: '誕生月',
  };
  const methodLabel = methodLabelMap[method] || '';
  addMsg(methodLabel, true);

  let options: string[] = [];
  if (method === 'color') {
    options = ['紫', 'ピンク', '黄', '透明', '黒', '水色', '紺', '茶金', '白', '赤'];
  } else if (method === 'effect') {
    options = ['愛情', '癒し', '金運', '浄化', '保護', '直感', '情熱', '女性性'];
  } else if (method === 'zodiac') {
    options = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座', '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座'];
  } else {
    options = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
  }

  addMsg(`${methodLabel}を選んでください`, false);

  let html = '<div class="btn-group">';
  for (const opt of options) {
    html += `<button class="btn-toggle" onclick="selectStoneOption('${opt}', this)">${opt}</button>`;
  }
  html += '</div><button class="btn" onclick="confirmStoneSelection()">この石で進む</button>';
  setInputArea(html);
}

/** 石オプション選択 */
export function selectStoneOption(option: string, el: HTMLElement): void {
  state.formData.stone_option = option;
  el.parentElement?.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

/** 石選択を確定 */
export function confirmStoneSelection(): void {
  const option = state.formData.stone_option;
  if (!option) {
    addMsg('選択してください', false);
    return;
  }
  addMsg(option, true);

  const stoneMap: Record<string, string> = {
    '紫': 'アメジスト', 'ピンク': 'ローズクォーツ', '黄': 'シトリン', '透明': '水晶',
    '黒': 'オニキス', '水色': 'アクアマリン', '紺': 'ラピスラズリ', '茶金': 'タイガーアイ',
    '白': 'ムーンストーン', '赤': 'カーネリアン',
  };
  const selectedStone = stoneMap[option] || 'アメジスト';

  state.divinationResult = {
    stones_for_user: [
      { name: selectedStone, reason: `${option}を選んだあなたにぴったりの石です` },
    ],
  };

  stepOrderChoice();
}

/** 注文方法選択 */
function stepOrderChoice(): void {
  addMsg('ブレスレットの注文方法を選んでください。', false);
  setInputArea(`
    <button class="btn" onclick="selectOrderType('custom')">✨ オーダーメイド（カスタマイズ）</button>
    <button class="btn btn-secondary" onclick="selectOrderType('shop')">🛒 ネットショップから選ぶ</button>
  `);
}

/** 注文方法を選択 */
export function selectOrderType(type: string): void {
  if (type === 'custom') {
    addMsg('オーダーメイド（カスタマイズ）', true);
    stepBraceletSize();
  } else {
    addMsg('ネットショップから選ぶ', true);
    addMsg('今の診断結果に関連するブレスレットを、ネットショップでお見せしますね。', false);

    const method = state.formData.stone_method;
    const option = state.formData.stone_option;

    const categoryUrlMap: Record<string, Record<string, string>> = {
      color: {
        '紫': 'https://spicastar.info/atlas/shop/product-category/color-purple/',
        'ピンク': 'https://spicastar.info/atlas/shop/product-category/color-pink/',
        '黄': 'https://spicastar.info/atlas/shop/product-category/color-yellow/',
        '透明': 'https://spicastar.info/atlas/shop/product-category/color-clear/',
        '黒': 'https://spicastar.info/atlas/shop/product-category/color-black/',
        '水色': 'https://spicastar.info/atlas/shop/product-category/color-lightblue/',
        '紺': 'https://spicastar.info/atlas/shop/product-category/color-navy/',
        '茶金': 'https://spicastar.info/atlas/shop/product-category/color-brown-gold/',
        '白': 'https://spicastar.info/atlas/shop/product-category/color-white/',
        '赤': 'https://spicastar.info/atlas/shop/product-category/color-red/',
      },
      effect: {
        '愛情': 'https://spicastar.info/atlas/shop/product-category/effect-love/',
        '癒し': 'https://spicastar.info/atlas/shop/product-category/effect-healing/',
        '金運': 'https://spicastar.info/atlas/shop/product-category/effect-money/',
        '浄化': 'https://spicastar.info/atlas/shop/product-category/effect-purify/',
        '保護': 'https://spicastar.info/atlas/shop/product-category/effect-protection/',
        '直感': 'https://spicastar.info/atlas/shop/product-category/effect-intuition/',
        '情熱': 'https://spicastar.info/atlas/shop/product-category/effect-passion/',
        '女性性': 'https://spicastar.info/atlas/shop/product-category/effect-femininity/',
      },
      zodiac: {
        '牡羊座': 'https://spicastar.info/atlas/shop/product-category/zodiac-aries/',
        '牡牛座': 'https://spicastar.info/atlas/shop/product-category/zodiac-taurus/',
        '双子座': 'https://spicastar.info/atlas/shop/product-category/zodiac-gemini/',
        '蟹座': 'https://spicastar.info/atlas/shop/product-category/zodiac-cancer/',
        '獅子座': 'https://spicastar.info/atlas/shop/product-category/zodiac-leo/',
        '乙女座': 'https://spicastar.info/atlas/shop/product-category/zodiac-virgo/',
        '天秤座': 'https://spicastar.info/atlas/shop/product-category/zodiac-libra/',
        '蠍座': 'https://spicastar.info/atlas/shop/product-category/zodiac-scorpio/',
        '射手座': 'https://spicastar.info/atlas/shop/product-category/zodiac-sagittarius/',
        '山羊座': 'https://spicastar.info/atlas/shop/product-category/zodiac-capricorn/',
        '水瓶座': 'https://spicastar.info/atlas/shop/product-category/zodiac-aquarius/',
        '魚座': 'https://spicastar.info/atlas/shop/product-category/zodiac-pisces/',
      },
      moon: {
        '1月': 'https://spicastar.info/atlas/shop/product-category/moon-january/',
        '2月': 'https://spicastar.info/atlas/shop/product-category/moon-february/',
        '3月': 'https://spicastar.info/atlas/shop/product-category/moon-march/',
        '4月': 'https://spicastar.info/atlas/shop/product-category/moon-april/',
        '5月': 'https://spicastar.info/atlas/shop/product-category/moon-may/',
        '6月': 'https://spicastar.info/atlas/shop/product-category/moon-june/',
        '7月': 'https://spicastar.info/atlas/shop/product-category/moon-july/',
        '8月': 'https://spicastar.info/atlas/shop/product-category/moon-august/',
        '9月': 'https://spicastar.info/atlas/shop/product-category/moon-september/',
        '10月': 'https://spicastar.info/atlas/shop/product-category/moon-october/',
        '11月': 'https://spicastar.info/atlas/shop/product-category/moon-november/',
        '12月': 'https://spicastar.info/atlas/shop/product-category/moon-december/',
      },
    };

    let url = 'https://spicastar.info/atlas/shop/';
    if (method && option && categoryUrlMap[method] && categoryUrlMap[method][option]) {
      url = categoryUrlMap[method][option];
      const params = new URLSearchParams({ from: 'atlas-chat', method, choice: option });
      url = `${url}?${params.toString()}`;
    }
    window.location.href = url;
  }
}

/** 最初からやり直す */
export function restartFromBeginning(): void {
  const box = document.getElementById('chatBox');
  if (box) box.innerHTML = '';

  addMsg(getGreetingMessage(), false);
  loadProfileFromLocalStorage();
  stepModeSelect();
}
