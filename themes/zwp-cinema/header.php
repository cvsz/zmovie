<!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="zwpc-skip" href="#main"><?php esc_html_e('Skip to cinema feed', 'zwp-cinema'); ?></a>
<header class="zwpc-header">
    <div class="zwpc-brand">
        <?php if (has_custom_logo()) : the_custom_logo(); else : ?>
            <a href="<?php echo esc_url(home_url('/')); ?>" class="zwpc-wordmark" rel="home">Z<span>✦</span>CINEMA</a>
        <?php endif; ?>
        <small><?php esc_html_e('Stories worth watching', 'zwp-cinema'); ?></small>
    </div>
    <nav class="zwpc-nav" aria-label="<?php esc_attr_e('Main navigation', 'zwp-cinema'); ?>">
        <a href="<?php echo esc_url(home_url('/')); ?>"><?php esc_html_e('Discover', 'zwp-cinema'); ?></a>
        <?php if (post_type_exists('zwpc_film')) : ?>
            <a href="<?php echo esc_url(get_post_type_archive_link('zwpc_film')); ?>"><?php esc_html_e('Films', 'zwp-cinema'); ?></a>
        <?php endif; ?>
        <?php if (has_nav_menu('primary')) : wp_nav_menu(array('theme_location' => 'primary',
            'container' => false, 'items_wrap' => '<ul class="zwpc-menu">%3$s</ul>')); endif; ?>
    </nav>
    <div class="zwpc-header-right">
        <?php if (is_user_logged_in()) : ?>
            <a href="<?php echo esc_url(admin_url('profile.php')); ?>"><?php esc_html_e('My account', 'zwp-cinema'); ?></a>
        <?php else : ?>
            <a class="zwpc-pill" href="<?php echo esc_url(wp_login_url(home_url('/'))); ?>"><?php esc_html_e('Sign in', 'zwp-cinema'); ?></a>
        <?php endif; ?>
    </div>
</header>
