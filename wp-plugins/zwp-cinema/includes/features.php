<?php
/**
 * ZeaZ Cinema additional features.
 *
 * @package ZeaZ Cinema
 * @since 0.2.0
 */
defined('ABSPATH') || exit;

/**
 * Add custom meta fields for films.
 */
function zwpc_add_film_meta() {
    // Runtime
    register_post_meta('zwpc_film', 'zwpc_runtime', array(
        'single' => true, 'type' => 'integer', 'show_in_rest' => true,
        'sanitize_callback' => 'absint',
    ));

    // Age rating
    register_post_meta('zwpc_film', 'zwpc_age_rating', array(
        'single' => true, 'type' => 'string', 'show_in_rest' => true,
        'sanitize_callback' => 'sanitize_text_field',
    ));

    // Poster URL
    register_post_meta('zwpc_film', 'zwpc_poster_url', array(
        'single' => true, 'type' => 'string', 'show_in_rest' => true,
        'sanitize_callback' => 'esc_url_raw',
    ));

    // Release date
    register_post_meta('zwpc_film', 'zwpc_release_date', array(
        'single' => true, 'type' => 'string', 'show_in_rest' => true,
        'sanitize_callback' => 'sanitize_text_field',
    ));

    // Creator
    register_post_meta('zwpc_film', 'zwpc_creator', array(
        'single' => true, 'type' => 'string', 'show_in_rest' => true,
        'sanitize_callback' => 'sanitize_text_field',
    ));

    // Copyright/rights
    register_post_meta('zwpc_film', 'zwpc_rights', array(
        'single' => true, 'type' => 'string', 'show_in_rest' => true,
        'sanitize_callback' => 'sanitize_text_field',
    ));
}
add_action('init', 'zwpc_add_film_meta');

/**
 * Add custom columns to the film edit screen.
 */
function zwpc_manage_film_columns($columns) {
    $new_columns = array(
        'cb'          => '<input type="checkbox" />',
        'title'       => __('Film Title', 'zwp-cinema'),
        'genre'       => __('Genre', 'zwp-cinema'),
        'runtime'     => __('Runtime', 'zwp-cinema'),
        'age_rating'  => __('Age Rating', 'zwp-cinema'),
        'author'      => __('Creator', 'zwp-cinema'),
        'date'        => __('Date', 'zwp-cinema'),
    );
    return $new_columns;
}
add_filter('manage_zwpc_film_posts_columns', 'zwpc_manage_film_columns');

/**
 * Populate custom columns.
 */
function zwpc_manage_film_custom_column($column, $post_id) {
    switch ($column) {
        case 'genre':
            $terms = wp_get_post_terms($post_id, 'zwpc_genre', array('fields' => 'names'));
            echo esc_html(implode(', ', $terms));
            break;
        case 'runtime':
            $runtime = get_post_meta($post_id, 'zwpc_runtime', true);
            echo $runtime ? esc_html($runtime) . ' min' : '—';
            break;
        case 'age_rating':
            $rating = get_post_meta($post_id, 'zwpc_age_rating', true);
            echo $rating ? esc_html($rating) : '—';
            break;
        case 'author':
            $creator = get_post_meta($post_id, 'zwpc_creator', true);
            echo $creator ? esc_html($creator) : get_the_author();
            break;
    }
}
add_action('manage_zwpc_film_posts_custom_column', 'zwpc_manage_film_custom_column', 10, 2);

/**
 * Register creator user role.
 */
function zwpc_register_creator_role() {
    add_role('creator', __('Creator', 'zwp-cinema'), array(
        'read' => true,
        'edit_posts' => true,
        'edit_others_posts' => false,
        'publish_posts' => false,
        'upload_files' => true,
        'edit_zwpc_film' => true,
        'read_zwpc_film' => true,
    ));
}
add_action('init', 'zwpc_register_creator_role');

/**
 * Add creator profile fields.
 */
function zwpc_add_creator_profile_fields($user) {
    if (!current_user_can('creator')) return;
    ?>
    <h3><?php esc_html_e('Creator Profile', 'zwp-cinema'); ?></h3>
    <table class="form-table">
        <tr>
            <th><label for="zwpc_creator_bio"><?php esc_html_e('Bio', 'zwp-cinema'); ?></label></th>
            <td><textarea name="zwpc_creator_bio" id="zwpc_creator_bio" rows="4" class="regular-text"><?php echo esc_textarea(get_the_author_meta('zwpc_creator_bio', $user->ID)); ?></textarea></td>
        </tr>
        <tr>
            <th><label for="zwpc_creator_website"><?php esc_html_e('Website', 'zwp-cinema'); ?></label></th>
            <td><input type="url" name="zwpc_creator_website" id="zwpc_creator_website" value="<?php echo esc_url(get_the_author_meta('zwpc_creator_website', $user->ID)); ?>" class="regular-text" /></td>
        </tr>
    </table>
    <?php
}
add_action('show_user_profile', 'zwpc_add_creator_profile_fields');
add_action('edit_user_profile', 'zwpc_add_creator_profile_fields');

function zwpc_save_creator_profile_fields($user_id) {
    if (!current_user_can('edit_user', $user_id)) return;
    update_user_meta($user_id, 'zwpc_creator_bio', sanitize_textarea_field($_POST['zwpc_creator_bio'] ?? ''));
    update_user_meta($user_id, 'zwpc_creator_website', esc_url_raw($_POST['zwpc_creator_website'] ?? ''));
}
add_action('personal_options_update', 'zwpc_save_creator_profile_fields');
add_action('edit_user_profile_update', 'zwpc_save_creator_profile_fields');
