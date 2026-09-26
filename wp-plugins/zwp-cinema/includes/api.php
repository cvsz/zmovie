<?php
/**
 * ZeaZ Cinema REST API endpoints.
 *
 * @package ZeaZ Cinema
 * @since 0.1.0
 */
defined('ABSPATH') || exit;

/**
 * Register custom REST routes.
 */
function zwpc_register_api_routes() {
    // Feed endpoint
    register_rest_route('zwpc/v1', '/feed', array(
        'methods'  => WP_REST_Server::READABLE,
        'callback' => 'zwpc_feed_endpoint',
        'permission_callback' => '__return_true',
        'args'     => array(
            'page'     => array('type' => 'integer', 'default' => 1),
            'per_page' => array('type' => 'integer', 'default' => 12),
            'genre'    => array('type' => 'string', 'default' => ''),
            'search'   => array('type' => 'string', 'default' => ''),
        ),
    ));

    // Favorites endpoint
    register_rest_route('zwpc/v1', '/favorites', array(
        'methods'  => WP_REST_Server::CREATABLE,
        'callback' => 'zwpc_favorites_endpoint',
        'permission_callback' => function() { return is_user_logged_in(); },
        'args'     => array(
            'film_id' => array('type' => 'integer', 'required' => true),
        ),
    ));
    register_rest_route('zwpc/v1', '/favorites', array(
        'methods'  => WP_REST_Server::DELETABLE,
        'callback' => 'zwpc_favorites_delete_endpoint',
        'permission_callback' => function() { return is_user_logged_in(); },
        'args'     => array(
            'film_id' => array('type' => 'integer', 'required' => true),
        ),
    ));
    register_rest_route('zwpc/v1', '/favorites', array(
        'methods'  => WP_REST_Server::READABLE,
        'callback' => 'zwpc_favorites_list_endpoint',
        'permission_callback' => function() { return is_user_logged_in(); },
    ));

    // Submit film endpoint
    register_rest_route('zwpc/v1', '/submit-film', array(
        'methods'  => WP_REST_Server::CREATABLE,
        'callback' => 'zwpc_submit_film_endpoint',
        'permission_callback' => function() { return is_user_logged_in() && zwpc_license_has_feature('creator_submission'); },
        'args'     => array(
            'title'     => array('type' => 'string', 'required' => true),
            'description' => array('type' => 'string'),
            'genre'     => array('type' => 'string'),
            'video_url' => array('type' => 'string'),
            'poster_url'=> array('type' => 'string'),
            'runtime'   => array('type' => 'integer'),
            'age_rating'=> array('type' => 'string'),
        ),
    ));
}
add_action('rest_api_init', 'zwpc_register_api_routes');

/**
 * Feed endpoint: returns films with filtering.
 */
function zwpc_feed_endpoint($request) {
    $args = array(
        'post_type'      => 'zwpc_film',
        'posts_per_page' => $request['per_page'],
        'paged'          => $request['page'],
        'post_status'    => 'publish',
        'orderby'        => 'date',
        'order'          => 'DESC',
    );

    if (!empty($request['genre'])) {
        $args['tax_query'] = array(array(
            'taxonomy' => 'zwpc_genre',
            'field'    => 'slug',
            'terms'    => sanitize_text_field($request['genre']),
        ));
    }

    if (!empty($request['search'])) {
        $args['s'] = sanitize_text_field($request['search']);
    }

    $query = new WP_Query($args);
    $films = array();

    while ($query->have_posts()) {
        $query->the_post();
        $film_id = get_the_ID();
        $films[] = array(
            'id'          => $film_id,
            'title'       => get_the_title(),
            'excerpt'     => get_the_excerpt(),
            'poster_url'  => get_the_post_thumbnail_url($film_id, 'large') ?: '',
            'video_url'   => get_post_meta($film_id, 'zwpc_video_url', true),
            'genre'       => wp_get_post_terms($film_id, 'zwpc_genre', array('fields' => 'names')),
            'runtime'     => get_post_meta($film_id, 'zwpc_runtime', true),
            'age_rating'  => get_post_meta($film_id, 'zwpc_age_rating', true),
            'author'      => get_the_author(),
            'date'        => get_the_date('c'),
            'permalink'   => get_permalink(),
            'is_favorite' => is_user_logged_in() ? (bool) get_user_meta(get_current_user_id(), 'zwpc_favorite_' . $film_id, true) : false,
        );
    }
    wp_reset_postdata();

    return new WP_REST_Response(array(
        'films'     => $films,
        'total'     => $query->found_posts,
        'page'      => $request['page'],
        'per_page'  => $request['per_page'],
    ), 200);
}

/**
 * Add favorite.
 */
function zwpc_favorites_endpoint($request) {
    $user_id = get_current_user_id();
    $film_id = intval($request['film_id']);
    $film = get_post($film_id);

    if (!$film || $film->post_type !== 'zwpc_film') {
        return new WP_REST_Response(array('error' => 'Invalid film'), 400);
    }

    update_user_meta($user_id, 'zwpc_favorite_' . $film_id, true);

    return new WP_REST_Response(array('success' => true, 'film_id' => $film_id), 200);
}

/**
 * Remove favorite.
 */
function zwpc_favorites_delete_endpoint($request) {
    $user_id = get_current_user_id();
    $film_id = intval($request['film_id']);
    delete_user_meta($user_id, 'zwpc_favorite_' . $film_id);

    return new WP_REST_Response(array('success' => true, 'film_id' => $film_id), 200);
}

/**
 * List favorites.
 */
function zwpc_favorites_list_endpoint($request) {
    $user_id = get_current_user_id();
    $favorites = get_user_meta($user_id);
    $favorite_ids = array();

    foreach ($favorites as $key => $value) {
        if (strpos($key, 'zwpc_favorite_') === 0 && $value[0]) {
            $favorite_ids[] = intval(str_replace('zwpc_favorite_', '', $key));
        }
    }

    $films = array();
    foreach ($favorite_ids as $id) {
        $film = get_post($id);
        if ($film && $film->post_type === 'zwpc_film') {
            $films[] = array(
                'id'         => $id,
                'title'      => $film->post_title,
                'poster_url' => get_the_post_thumbnail_url($id, 'medium') ?: '',
                'permalink'  => get_permalink($id),
            );
        }
    }

    return new WP_REST_Response(array('favorites' => $films), 200);
}

/**
 * Submit a film (creator submission).
 */
function zwpc_submit_film_endpoint($request) {
    $user_id = get_current_user_id();

    // Check license entitlement
    if (!zwpc_license_has_feature('creator_submission')) {
        return new WP_REST_Response(array('error' => 'License does not allow film submission'), 403);
    }

    $film_id = wp_insert_post(array(
        'post_title'   => sanitize_text_field($request['title']),
        'post_content' => sanitize_textarea_field($request['description'] ?? ''),
        'post_type'    => 'zwpc_film',
        'post_status'  => 'pending', // Requires moderator approval
        'post_author'  => $user_id,
    ));

    if (is_wp_error($film_id)) {
        return new WP_REST_Response(array('error' => $film_id->get_error_message()), 400);
    }

    // Set genre if provided
    if (!empty($request['genre'])) {
        wp_set_object_terms($film_id, sanitize_text_field($request['genre']), 'zwpc_genre');
    }

    // Set video URL
    if (!empty($request['video_url'])) {
        update_post_meta($film_id, 'zwpc_video_url', esc_url_raw($request['video_url']));
    }

    // Set poster URL
    if (!empty($request['poster_url'])) {
        update_post_meta($film_id, 'zwpc_poster_url', esc_url_raw($request['poster_url']));
    }

    // Set runtime
    if (!empty($request['runtime'])) {
        update_post_meta($film_id, 'zwpc_runtime', intval($request['runtime']));
    }

    // Set age rating
    if (!empty($request['age_rating'])) {
        update_post_meta($film_id, 'zwpc_age_rating', sanitize_text_field($request['age_rating']));
    }

    return new WP_REST_Response(array(
        'success'     => true,
        'film_id'     => $film_id,
        'post_status' => 'pending',
        'message'     => 'Film submitted for review',
    ), 201);
}
