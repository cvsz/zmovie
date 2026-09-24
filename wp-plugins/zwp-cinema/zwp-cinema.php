<?php
/**
 * Plugin Name: ZeaZ Cinema
 * Description: First-party cinema film catalog, trailer feed, favorites and licensed creator submissions.
 * Version: 0.1.0
 * Requires at least: 6.4
 * Requires PHP: 8.1
 * Text Domain: zwp-cinema
 * License: MIT
 */
defined('ABSPATH') || exit;
define('ZWPC_VERSION', '0.1.0');
define('ZWPC_PATH', plugin_dir_path(__FILE__));
require_once ZWPC_PATH . 'includes/license.php';

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
    $role = get_role('administrator');
    if ($role) {
        foreach (array('edit_zwpc_films', 'edit_others_zwpc_films', 'publish_zwpc_films',
            'read_private_zwpc_films', 'delete_zwpc_films', 'delete_others_zwpc_films',
            'edit_published_zwpc_films', 'delete_published_zwpc_films',
            'edit_private_zwpc_films', 'delete_private_zwpc_films') as $cap) {
            $role->add_cap($cap);
        }
    }
    flush_rewrite_rules();
}
register_activation_hook(__FILE__, 'zwpc_activate');
register_deactivation_hook(__FILE__, 'flush_rewrite_rules');

function zwpc_video_metabox() {
    add_meta_box('zwpc_video', __('Cinema trailer MP4 / WebM', 'zwp-cinema'), function($post) {
        wp_nonce_field('zwpc_save_video', 'zwpc_video_nonce');
        echo '<p><label for="zwpc_video_url">' . esc_html__('HTTPS URL to licensed, directly playable media', 'zwp-cinema') . '</label></p>';
        echo '<input id="zwpc_video_url" name="zwpc_video_url" type="url" class="widefat" value="' .
            esc_attr(get_post_meta($post->ID, 'zwpc_video_url', true)) . '">';
    }, 'zwpc_film', 'normal');
}
add_action('add_meta_boxes', 'zwpc_video_metabox');
add_action('save_post_zwpc_film', function($post_id) {
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }
    if (!isset($_POST['zwpc_video_nonce']) ||
        !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['zwpc_video_nonce'])), 'zwpc_save_video') ||
        !current_user_can('edit_post', $post_id)) {
        return;
    }
    if (isset($_POST['zwpc_video_url'])) {
        $url = zwpc_valid_video_url(wp_unslash($_POST['zwpc_video_url']));
        if ($url) {
            update_post_meta($post_id, 'zwpc_video_url', $url);
        } else {
            delete_post_meta($post_id, 'zwpc_video_url');
        }
    }
});

function zwpc_film_data($post_id) {
    $post = get_post($post_id);
    if (!$post || $post->post_type !== 'zwpc_film' || $post->post_status !== 'publish') {
        return null;
    }
    $genres = wp_get_post_terms($post_id, 'zwpc_genre', array('fields' => 'names'));
    return array(
        'id' => (int) $post_id,
        'title' => get_the_title($post_id),
        'excerpt' => wp_strip_all_tags(get_the_excerpt($post_id)),
        'url' => get_permalink($post_id),
        'video' => zwpc_valid_video_url(get_post_meta($post_id, 'zwpc_video_url', true)),
        'poster' => get_the_post_thumbnail_url($post_id, 'large') ?: '',
        'creator' => get_the_author_meta('display_name', (int) $post->post_author),
        'genres' => is_wp_error($genres) ? array() : $genres,
    );
}

function zwpc_register_api() {
    register_rest_route('zwpc/v1', '/feed', array(
        'methods' => 'GET', 'permission_callback' => '__return_true',
        'callback' => function(WP_REST_Request $request) {
            $page = (int) $request->get_param('page');
            $page = max(1, min(100, $page));
            $args = array(
                'post_type' => 'zwpc_film', 'post_status' => 'publish',
                'posts_per_page' => 6, 'paged' => $page, 'no_found_rows' => false,
                'orderby' => 'date', 'order' => 'DESC',
            );
            $genre = sanitize_title((string) $request->get_param('genre'));
            if ($genre !== '') {
                $args['tax_query'] = array(array('taxonomy' => 'zwpc_genre', 'field' => 'slug', 'terms' => $genre));
            }
            $query = new WP_Query($args);
            $items = array();
            foreach ($query->posts as $post) {
                $film = zwpc_film_data($post->ID);
                if ($film !== null) {
                    $items[] = $film;
                }
            }
            return rest_ensure_response(array(
                'items' => $items, 'page' => $page,
                'has_more' => $page < (int) $query->max_num_pages,
            ));
        },
        'args' => array(
            'page' => array('sanitize_callback' => 'absint'),
            'genre' => array('sanitize_callback' => 'sanitize_title'),
        ),
    ));
    register_rest_route('zwpc/v1', '/favorites', array(
        'methods' => 'GET',
        'permission_callback' => function() { return is_user_logged_in(); },
        'callback' => function() {
            $ids = array_map('absint', (array) get_user_meta(get_current_user_id(), 'zwpc_favorites', true));
            return rest_ensure_response(array_values(array_filter($ids, function($id) {
                return zwpc_film_data($id) !== null;
            })));
        },
    ));
    register_rest_route('zwpc/v1', '/favorites/(?P<id>\\d+)', array(
        'methods' => 'POST',
        'permission_callback' => function() { return is_user_logged_in(); },
        'callback' => function(WP_REST_Request $request) {
            $id = absint($request['id']);
            if (zwpc_film_data($id) === null) {
                return new WP_Error('zwpc_not_found', __('Film not found', 'zwp-cinema'), array('status' => 404));
            }
            $user = get_current_user_id();
            $ids = array_values(array_unique(array_map('absint',
                (array) get_user_meta($user, 'zwpc_favorites', true))));
            $saved = in_array($id, $ids, true);
            $ids = $saved ? array_values(array_diff($ids, array($id))) : array_slice(array_merge($ids, array($id)), -500);
            update_user_meta($user, 'zwpc_favorites', $ids);
            return rest_ensure_response(array('saved' => !$saved));
        },
    ));
}
add_action('rest_api_init', 'zwpc_register_api');

function zwpc_submit_shortcode() {
    if (!is_user_logged_in()) {
        return '<p>' . esc_html__('Please sign in to submit your film.', 'zwp-cinema') . '</p>';
    }
    if (!zwpc_license_has_feature('cinema.creator')) {
        return '<p>' . esc_html__('Creator submissions require an active ZeaZ Cinema Creator license.', 'zwp-cinema') . '</p>';
    }
    ob_start();
    if (isset($_GET['zwpc_status']) && $_GET['zwpc_status'] === 'received') {
        echo '<p role="status">' . esc_html__('Submitted for editorial review.', 'zwp-cinema') . '</p>';
    }
    ?>
    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" class="zwpc-form">
        <input type="hidden" name="action" value="zwpc_submit">
        <?php wp_nonce_field('zwpc_submit_film', 'zwpc_nonce'); ?>
        <p><label for="zwpc_title"><?php esc_html_e('Film title', 'zwp-cinema'); ?></label>
        <input required maxlength="180" id="zwpc_title" name="zwpc_title" type="text"></p>
        <p><label for="zwpc_description"><?php esc_html_e('Synopsis', 'zwp-cinema'); ?></label>
        <textarea id="zwpc_description" name="zwpc_description" maxlength="4000" rows="5"></textarea></p>
        <p><label for="zwpc_url"><?php esc_html_e('Licensed HTTPS MP4/WebM URL', 'zwp-cinema'); ?></label>
        <input required id="zwpc_url" name="zwpc_url" type="url" maxlength="2048"></p>
        <p><label><input type="checkbox" name="zwpc_rights" value="1" required>
        <?php esc_html_e('I own or have permission to submit this video for public display.', 'zwp-cinema'); ?></label></p>
        <button type="submit"><?php esc_html_e('Submit for review', 'zwp-cinema'); ?></button>
    </form>
    <?php
    return ob_get_clean();
}
add_shortcode('zwpc_submit', 'zwpc_submit_shortcode');
add_action('admin_post_zwpc_submit', function() {
    if (!is_user_logged_in() || !zwpc_license_has_feature('cinema.creator')) {
        wp_die(esc_html__('Not authorized to submit films.', 'zwp-cinema'), '', array('response' => 403));
    }
    check_admin_referer('zwpc_submit_film', 'zwpc_nonce');
    if (empty($_POST['zwpc_rights']) || $_POST['zwpc_rights'] !== '1') {
        wp_die(esc_html__('Rights confirmation is required.', 'zwp-cinema'), '', array('response' => 400));
    }
    $title = sanitize_text_field(wp_unslash($_POST['zwpc_title'] ?? ''));
    $description = sanitize_textarea_field(wp_unslash($_POST['zwpc_description'] ?? ''));
    $video = zwpc_valid_video_url(wp_unslash($_POST['zwpc_url'] ?? ''));
    if (!$video || !$title || (function_exists('mb_strlen') ? mb_strlen($title) : strlen($title)) > 180 ||
        (function_exists('mb_strlen') ? mb_strlen($description) : strlen($description)) > 4000) {
        wp_die(esc_html__('Invalid film submission.', 'zwp-cinema'), '', array('response' => 400));
    }
    $id = wp_insert_post(array(
        'post_type' => 'zwpc_film', 'post_title' => $title,
        'post_content' => $description, 'post_author' => get_current_user_id(),
        'post_status' => 'pending', 'meta_input' => array('zwpc_video_url' => $video),
    ), true);
    if (is_wp_error($id)) {
        wp_die(esc_html__('Could not submit film.', 'zwp-cinema'), '', array('response' => 500));
    }
    $return = wp_get_referer() ?: home_url('/');
    wp_safe_redirect(add_query_arg('zwpc_status', 'received', $return), 303);
    exit;
});
