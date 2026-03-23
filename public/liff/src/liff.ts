/**
 * LIFF（LINE Front-end Framework）初期化
 */

/** LIFF SDKの初期化 */
export async function initLiff(): Promise<void> {
  try {
    await liff.init({
      liffId: '2009078638-GZhFVgaz',
    });
    if (liff.isLoggedIn()) {
      const profile = await liff.getProfile();
      window.LINE_USER_ID = profile.userId;
    }
  } catch {
    console.log('LIFF not available');
  }
}

/** WooCommerce注文フォームにdiagnosis_idを埋め込む */
export function fillOrderNote(): void {
  const params = new URLSearchParams(window.location.search);
  const diagnosisId = params.get('d');
  if (!diagnosisId) return;

  const noteField = document.querySelector('#order_comments') as HTMLInputElement | null;
  if (noteField) {
    noteField.value = 'diagnosis_id:' + diagnosisId;
  }
}
