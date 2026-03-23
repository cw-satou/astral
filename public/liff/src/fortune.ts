/**
 * 今日の運勢モジュール
 */

import { state } from './state';
import { addMsg, setInputArea, clearInputArea } from './chat';
import { getUserNameForDisplay } from './profile';

/** 今日の運勢フローの入口 */
export async function stepTodayFortune(): Promise<void> {
  state.selectedMode = 'today_fortune';
  await addMsg(
    '今日の運勢を読むために、生年月日・生まれた時間と場所を教えていただけますか？',
    false
  );
  // showAstrologicalInfoForm は steps.ts から呼ばれる
}

/** 今日のコメント送信 */
export function submitTodayComment(): void {
  const textarea = document.getElementById('todayComment') as HTMLTextAreaElement | null;
  const comment = (textarea && textarea.value.trim()) || '';
  if (comment) {
    addMsg(comment, true);
    state.formData.today_comment = comment;
  }
  clearInputArea();
  addMsg(
    'ありがとうございます。\nでは、この流れを踏まえて、今日はどんなテーマについて詳しく見ていきましょうか？',
    false
  );
}

/** 今日の運勢を実行 */
export async function runTodayFortune(): Promise<void> {
  const birth = state.formData.birth || {};
  await addMsg(
    '生まれた時間と場所も含めて、AIに今日の運勢を聞いてみますね。',
    false
  );
  setInputArea(`
    <div class="loading">
      <div class="spinner"></div>
      <p>今日の運勢を読み解いています... 🔮</p>
    </div>
  `);

  try {
    const res = await fetch('/api/today-fortune', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gender: state.formData.gender,
        birth: birth,
      }),
    });

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}`);
    }

    const json = await res.json();

    if (json.error) {
      clearInputArea();
      await addMsg(
        `占いの処理中にエラーが発生しました:\n${json.error}`,
        false
      );
      setInputArea(`
        <button class="btn btn-secondary" onclick="restartFromBeginning()">
          🔄 最初に戻る
        </button>
      `);
      return;
    }

    const rawMessage =
      json.message ||
      '今日は、自分のペースを大切に過ごすと良さそうな日です。';
    const fortuneText = extractFortuneFromMessage(rawMessage);

    clearInputArea();
    await addMsg(`【今日の運勢】\n${fortuneText}`, false);
    await addMsg(
      'この流れを踏まえて、あなたの導きの天然石を診断してみますか？',
      false
    );
    setInputArea(`
      <button class="btn" onclick="selectMode('divination')">
        💎 導きの天然石を診断する
      </button>
      <button class="btn btn-secondary" onclick="restartFromBeginning()">
        🔄 最初に戻る
      </button>
    `);
  } catch {
    clearInputArea();
    await addMsg(
      'AIにうまくアクセスできませんでした。\n少し時間をおいてからもう一度お試しください。',
      false
    );
    setInputArea(`
      <button class="btn" onclick="restartFromBeginning()">🔄 最初に戻る</button>
    `);
  }
}

/** AIレスポンスから運勢テキストを抽出 */
function extractFortuneFromMessage(raw: string): string {
  if (!raw) return '';
  const cleaned = raw
    .replace(/```json/g, '')
    .replace(/```/g, '')
    .trim();
  try {
    const obj = JSON.parse(cleaned);
    return obj.鑑定結果 || cleaned;
  } catch {
    return cleaned;
  }
}
