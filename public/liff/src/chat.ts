/**
 * チャットUI管理
 * メッセージの表示、タイピングエフェクト、スクロール制御
 */

import { state } from './state';

/** チャットボックスの最下部にスクロール */
export function scrollChatToBottom(): void {
  const box = document.getElementById('chatBox');
  if (!box) return;
  box.scrollTop = box.scrollHeight;
}

/** テキストのフォーマット（Markdown風の強調変換） */
export function formatText(text: string): string {
  if (!text) return '';
  const decoded = text
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
  return decoded.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

/** タイピングエフェクト付きテキスト表示 */
export function typeText(element: HTMLElement, text: string, speed = 40): Promise<void> {
  return new Promise((resolve) => {
    const plain = text
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]*>/g, '');
    let i = 0;
    function type(): void {
      if (i < plain.length) {
        element.textContent = plain.slice(0, i + 1);
        i++;
        scrollChatToBottom();
        setTimeout(type, speed);
      } else {
        element.innerHTML = text;
        resolve();
      }
    }
    type();
  });
}

/** メッセージをチャットに追加（キュー制御付き） */
export function addMsg(text: string, isUser = false): Promise<void> {
  state.messageQueue = state.messageQueue.then(() => renderMessage(text, isUser));
  return state.messageQueue;
}

/** メッセージを描画する */
function renderMessage(text: string, isUser: boolean): Promise<void> {
  return new Promise((resolve) => {
    const box = document.getElementById('chatBox');
    if (!box) { resolve(); return; }

    const div = document.createElement('div');
    div.className = `msg ${isUser ? 'user' : 'bot'}`;
    box.appendChild(div);

    const formatted = formatText(text.replace(/\n/g, '<br>'));

    if (isUser) {
      div.innerHTML = formatted;
      scrollChatToBottom();
      resolve();
      return;
    }

    typeText(div, formatted, 40).then(() => {
      scrollChatToBottom();
      resolve();
    });
  });
}

/** 入力エリアにHTMLを設定 */
export function setInputArea(html: string): void {
  const el = document.getElementById('inputArea');
  if (el) el.innerHTML = html;
  scrollChatToBottom();
}

/** 入力エリアをクリア */
export function clearInputArea(): void {
  setInputArea('');
}

/** プログレスバーを更新 */
export function setProgress(step: number, total: number, label: string): void {
  const el = document.getElementById('progressBar');
  if (el) {
    el.innerHTML = `STEP ${step} / ${total}<br>${label}`;
  }
}
