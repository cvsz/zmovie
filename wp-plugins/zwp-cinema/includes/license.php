<?php
/**
 * First-party ZeaZDev license client. Never intercepts or substitutes WP-Script keys.
 *
 * Configure in wp-config.php or a secret manager:
 * ZEAZ_LICENSE_API, ZEAZ_LICENSE_ORIGIN, ZEAZ_LICENSE_KEY,
 * ZEAZ_LICENSE_PUBLIC_KEY (base64url Ed25519, pinned out of band).
 */
defined('ABSPATH') || exit;

function zwpc_license_claims() {
    if (!function_exists('sodium_crypto_sign_verify_detached') ||
        !defined('ZEAZ_LICENSE_API') || !defined('ZEAZ_LICENSE_ORIGIN') ||
        !defined('ZEAZ_LICENSE_KEY') || !defined('ZEAZ_LICENSE_PUBLIC_KEY')) {
        return false;
    }
    $origin = rtrim(strtolower((string) ZEAZ_LICENSE_ORIGIN), '/');
    $home = wp_parse_url(home_url('/'));
    $home_origin = strtolower(($home['scheme'] ?? '') . '://' . ($home['host'] ?? ''));
    if (isset($home['port'])) {
        $home_origin .= ':' . (int) $home['port'];
    }
    if (!hash_equals($home_origin, $origin)) {
        return false;
    }
    $api = (string) ZEAZ_LICENSE_API;
    if (wp_parse_url($api, PHP_URL_SCHEME) !== 'https') {
        return false;
    }
    $cache_key = 'zwpc_lease_' . md5($origin);
    $token = get_transient($cache_key);
    if (!is_string($token) || !$token) {
        $response = wp_remote_post(rtrim($api, '/') . '/v1/activate', array(
            'timeout' => 5,
            'redirection' => 0,
            'headers' => array('Content-Type' => 'application/json'),
            'body' => wp_json_encode(array(
                'key' => ZEAZ_LICENSE_KEY,
                'product' => 'zmovie',
                'site_url' => $origin,
            )),
        ));
        if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
            return false;
        }
        $body = json_decode(wp_remote_retrieve_body($response), true);
        if (!is_array($body) || empty($body['lease']) || !is_string($body['lease'])) {
            return false;
        }
        $token = $body['lease'];
    }
    $parts = explode('.', $token);
    if (count($parts) !== 3) {
        return false;
    }
    try {
        $header = json_decode(sodium_base642bin($parts[0], SODIUM_BASE64_VARIANT_URLSAFE_NO_PADDING), true);
        $claims = json_decode(sodium_base642bin($parts[1], SODIUM_BASE64_VARIANT_URLSAFE_NO_PADDING), true);
        $signature = sodium_base642bin($parts[2], SODIUM_BASE64_VARIANT_URLSAFE_NO_PADDING);
        $pubkey = sodium_base642bin((string) ZEAZ_LICENSE_PUBLIC_KEY, SODIUM_BASE64_VARIANT_URLSAFE_NO_PADDING);
        if (!is_array($header) || !is_array($claims) ||
            array_keys($header) !== array('alg', 'kid', 'typ') ||
            $header['alg'] !== 'EdDSA' || $header['typ'] !== 'JWT' ||
            strlen($pubkey) !== SODIUM_CRYPTO_SIGN_PUBLICKEYBYTES ||
            !sodium_crypto_sign_verify_detached($signature, $parts[0] . '.' . $parts[1], $pubkey)) {
            return false;
        }
        $now = time();
        foreach (array('iat', 'nbf', 'exp') as $field) {
            if (!isset($claims[$field]) || !is_int($claims[$field])) {
                return false;
            }
        }
        if (($claims['iss'] ?? '') !== 'zeaz-license' ||
            ($claims['aud'] ?? '') !== 'zmovie' ||
            ($claims['site'] ?? '') !== $origin ||
            empty($claims['sub']) || empty($claims['activation_id']) ||
            $claims['iat'] > $now + 30 || $claims['nbf'] > $now + 30 ||
            $claims['exp'] <= $now || $claims['exp'] - $claims['iat'] > 900 ||
            !isset($claims['features']) || !is_array($claims['features'])) {
            return false;
        }
        set_transient($cache_key, $token, min(60, max(1, $claims['exp'] - $now)));
        return $claims;
    } catch (Throwable $error) {
        return false;
    }
}

function zwpc_license_has_feature($feature) {
    $claims = zwpc_license_claims();
    return is_array($claims) && in_array($feature, $claims['features'], true);
}
