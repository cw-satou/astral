<?php
/**
 * Plugin Name: Atlas Diagnosis Tracker
 * Plugin URI:  https://spicastar.info/atlas
 * Description: 星の羅針盤の診断IDをWooCommerce注文メタデータとして保存し、
 *              Webhookで診断データと注文を紐づけられるようにする。
 * Version:     1.0.0
 * Author:      Atlas
 */

defined('ABSPATH') || exit;

// ===== 1. URLパラメータ ?d= をセッション・Cookieに保存 =====
//
// ユーザーが診断結果から商品ページへ遷移するとき、
// フロントエンドが ?d={diagnosis_id} を付与する。
// このフックでそのパラメータを捕捉して保存する。

add_action('wp_loaded', function () {
    if (empty($_GET['d'])) {
        return;
    }

    // UUIDフォーマットのみ受け付ける（セキュリティ対策）
    $raw = sanitize_text_field(wp_unslash($_GET['d']));
    if (!preg_match('/^[0-9a-f\-]{32,36}$/i', $raw)) {
        return;
    }

    $diagnosis_id = $raw;

    // WooCommerceセッションに保存（カート〜チェックアウトまで保持）
    if (function_exists('WC') && WC()->session) {
        WC()->session->set('atlas_diagnosis_id', $diagnosis_id);
    }

    // Cookieにも保存（セッション切れのフォールバック、1時間有効）
    if (!headers_sent()) {
        setcookie(
            'atlas_diagnosis_id',
            $diagnosis_id,
            time() + 3600,
            '/',
            '',
            is_ssl(),
            true  // HttpOnly
        );
    }
});


// ===== 2. チェックアウト時に diagnosis_id を注文メタデータとして保存 =====
//
// WooCommerceが注文を作成する直前に呼ばれる。
// セッション → Cookie の順に diagnosis_id を取得し、
// 注文の meta_data として保存する（Webhookのペイロードに含まれる）。

add_action('woocommerce_checkout_create_order', function ($order, $data) {
    $diagnosis_id = '';

    // セッションから取得
    if (function_exists('WC') && WC()->session) {
        $diagnosis_id = WC()->session->get('atlas_diagnosis_id', '');
    }

    // セッションにない場合はCookieから取得
    if (empty($diagnosis_id) && !empty($_COOKIE['atlas_diagnosis_id'])) {
        $raw = sanitize_text_field(wp_unslash($_COOKIE['atlas_diagnosis_id']));
        if (preg_match('/^[0-9a-f\-]{32,36}$/i', $raw)) {
            $diagnosis_id = $raw;
        }
    }

    if (!empty($diagnosis_id)) {
        $order->update_meta_data('diagnosis_id', $diagnosis_id);
    }
}, 10, 2);


// ===== 3. 注文確定後にセッション・Cookieをクリア =====
//
// 同じブラウザで続けて別の診断をした場合に
// 前回の diagnosis_id が混入しないようにする。

add_action('woocommerce_checkout_order_created', function ($order) {
    if (function_exists('WC') && WC()->session) {
        WC()->session->__unset('atlas_diagnosis_id');
    }

    // Cookieを削除（過去の日時を指定することで削除）
    if (!headers_sent()) {
        setcookie('atlas_diagnosis_id', '', time() - 3600, '/', '', is_ssl(), true);
    }
});


// ===== 4. 注文詳細画面に diagnosis_id を表示（管理者向け） =====
//
// WooCommerce管理画面の注文詳細ページに診断IDを表示する。

add_action('woocommerce_admin_order_data_after_billing_address', function ($order) {
    $diagnosis_id = $order->get_meta('diagnosis_id');
    if (!$diagnosis_id) {
        return;
    }
    echo '<p><strong>診断ID（Atlas）：</strong>' . esc_html($diagnosis_id) . '</p>';
});
