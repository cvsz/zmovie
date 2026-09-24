<?php
/**
 * Plugin Name: ZeaZ Cinema
 * Description: First-party cinema film catalog, trailer feed, favorites and licensed creator submissions.
 * Version: 0.2.0
 * Requires at least: 6.4
 * Requires PHP: 8.1
 * Text Domain: zwp-cinema
 * License: MIT
 */
defined('ABSPATH') || exit;
define('ZWPC_VERSION', '0.2.0');
define('ZWPC_PATH', plugin_dir_path(__FILE__));
require_once ZWPC_PATH . 'includes/license.php';
require_once ZWPC_PATH . 'includes/api.php';
require_once ZWPC_PATH . 'includes/features.php';

function zwpc_register_content() {
    register_post_type('zwpc_film', array(
        'labels' => array('name' => __('Cinema Films', 'zwp-cinema'), 'singular_name' => __('Cinema Film', 'zwp-cinema')),
        'public' => true, 'show_in_rest' => true, 'has_archive' => true,
        'rewrite' => array('slug' => 'films'), 'menu_icon' => 'dashicons-video-alt3',
        'supports' => array('title', 'editor', 'thumbnail', 'comments', 'author', 'excerpt'),
        'capability_type' => array('zwpc_film', 'zwpc_films'), 'map_meta_cap' => true,
    ));
    register_taxonomy('zwpc_genre', 'zwpc_film', array(
        'labels' => array('name' => __('Genres', 'zwp-cinema')),
        'public' => true, 'show_in_rest' => true, 'hierarchical' => true,
        'rewrite' => array('slug' => 'genre'),
    ));
    register_post_meta('zwpc_film', 'zwpc_video_url', array(
        'single' => true, 'type' => 'string', 'show_in_rest' => false,
        'sanitize_callback' => 'zwpc_valid_video_url',
        'auth_callback' => function($allowed, $meta_key, $post_id) {
            return current_user_can('edit_post', $post_id);
        },
    ));
}
add_action('init', 'zwpc_register_content');

function zwpc_valid_video_url($url) {
    if (!is_string($url) || strlen($url) > 2048 || wp_parse_url($url, PHP_URL_SCHEME) !== 'https') {
        return '';
    }
    if (wp_parse_url($url, PHP_URL_USER) || wp_parse_url($url, PHP_URL_PASS)) {
        return '';
    }
    $path = (string) wp_parse_url($url, PHP_URL_PATH);
    return preg_match('/\\.(mp4|webm)$/i', $path) ? esc_url_raw($url, array('https')) : '';
}

function zwpc_activate() {
    zwpc_register_content();
    flush_rewrite_rules();
}
register_activation_hook(__FILE__, 'zwpc_activate');

function zwpc_deactivate() {
    flush_rewrite_rules();
}
register_deactivation_hook(__FILE__, 'zwpc_deactivate');
