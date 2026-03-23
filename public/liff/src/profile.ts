/**
 * プロフィール管理
 * ローカルストレージとサーバーへのプロフィール保存・読み込み
 */

import { state } from './state';

const PROFILE_STORAGE_KEY = 'hoshin-profile';
const USER_ID_COOKIE = 'hoshin_user_id';

/** プロフィールをLocalStorageとサーバーに保存 */
export function saveProfileToLocalStorage(): void {
  const profile = {
    name: state.formData.name,
    gender: state.formData.gender,
    birth: state.formData.birth,
    wrist_inner_cm: state.formData.wrist_inner_cm,
    bead_size_mm: state.formData.bead_size_mm,
    bracelet_type: state.formData.bracelet_type,
  };
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));

  if (state.userId) {
    fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: state.userId, ...profile }),
    }).catch(() => { /* サイレント失敗 */ });
  }
}

/** 表示用のユーザー名を取得 */
export function getUserNameForDisplay(): string {
  return (state.formData.name && state.formData.name.trim())
    ? `${state.formData.name.trim()}さん`
    : 'あなた';
}

/** Cookieを取得 */
export function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }
  return null;
}

/** Cookieを設定 */
export function setCookie(name: string, value: string, days = 365): void {
  const d = new Date();
  d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
  const expires = 'expires=' + d.toUTCString();
  document.cookie = `${name}=${value};${expires};path=/`;
}

/** 簡易UUID生成 */
export function generateUserId(): string {
  const s4 = (): string =>
    Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
  return `${s4()}${s4()}-${s4()}-${s4()}-${s4()}-${s4()}${s4()}${s4()}`;
}

/** 時間帯に応じた挨拶メッセージ */
export function getGreetingMessage(): string {
  const hour = new Date().getHours();
  const nameForDisplay = getUserNameForDisplay();
  if (hour >= 5 && hour < 11) {
    return `おはようございます。星の羅針盤「あとらす」です。\n今の気分や、ちょっと気になっていることがあれば、ここで整理してみませんか？\n\nあなたのお話と星の流れをもとに、今のあなたに合いそうな石や過ごし方のヒントをお伝えします。`;
  } else if (hour >= 11 && hour < 17) {
    return `こんにちは。星の羅針盤「あとらす」です。\n仕事や人間関係、これからのことなど、頭の中が少しごちゃごちゃしているときは、一度言葉にしてみるのがおすすめです。\n\nいま気になっていることを教えていただければ、星の配置とあわせて、落ち着いて考えるためのヒントをお出しします。`;
  } else {
    return `こんばんは。星の羅針盤「あとらす」です。\n一日の終わりに、心の中を少しだけ振り返ってみませんか。\n\nうまく言葉にならなくても大丈夫なので、気になっていることやモヤモヤしていることを、ここにそのまま書いてみてください。`;
  }
}

/** LocalStorageからプロフィールを復元 */
export function loadProfileFromLocalStorage(): void {
  const saved = localStorage.getItem(PROFILE_STORAGE_KEY);
  if (saved) {
    try {
      const localProfile = JSON.parse(saved);
      state.formData = { ...localProfile, ...state.formData };
    } catch {
      /* パースエラーは無視 */
    }
  }
}
