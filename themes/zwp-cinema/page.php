<?php get_header(); ?>
<main id="main" class="zwpc-film-page">
    <?php while (have_posts()) : the_post(); ?>
        <p class="zwpc-eyebrow"><?php esc_html_e('ZEA Z CINEMA', 'zwp-cinema'); ?></p>
        <h1><?php the_title(); ?></h1>
        <div class="entry-content"><?php the_content(); ?></div>
    <?php endwhile; ?>
</main>
<?php get_footer(); ?>
