<?php
/**
 * ZeaZ Cinema theme setup. Independent first-party code, not derived from TikSwipe sources.
 */
defined('ABSPATH') || exit;
define('ZWPC_THEME_VERSION', '0.1.0');

add_action('after_setup_theme', function() {
    load_theme_textdomain('zwp-cinema', get_template_directory() . '/languages');
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('responsive-embeds');
    add_theme_support('custom-logo', array('height' => 80, 'width' => 240, 'flex-height' => true, 'flex-width' => true));
    add_theme_support('html5', array('search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script'));
    register_nav_menus(array('primary' => __('Primary menu', 'zwp-cinema')));
});

add_action('wp_enqueue_scripts', function() {
    wp_enqueue_style('zwpc-cinema', get_stylesheet_uri(), array(), ZWPC_THEME_VERSION);
    wp_enqueue_script('zwpc-reels', get_template_directory_uri() . '/assets/js/reels.js', array(),
        ZWPC_THEME_VERSION, true);
    wp_add_inline_script('zwpc-reels', 'window.ZWPC=' . wp_json_encode(array(
        'api' => esc_url_raw(rest_url('zwpc/v1/')),
        'nonce' => wp_create_nonce('wp_rest'),
        'loggedIn' => is_user_logged_in(),
        'loginUrl' => wp_login_url(home_url('/')),
        'moreLabel' => __('Loading more films', 'zwp-cinema'),
        'emptyLabel' => __('No films found for this selection.', 'zwp-cinema'),
        'favoriteLabel' => __('Save to favorites', 'zwp-cinema'),
        'unfavoriteLabel' => __('Remove from favorites', 'zwp-cinema'),
    )) . ';', 'before');
});

add_action('admin_notices', function() {
    if (current_user_can('activate_plugins') && !post_type_exists('zwpc_film')) {
        echo '<div class="notice notice-warning"><p>' .
            esc_html__('ZeaZ Cinema theme needs the first-party ZeaZ Cinema plugin for films and the swipe feed.', 'zwp-cinema') .
            '</p></div>';
    }
});
