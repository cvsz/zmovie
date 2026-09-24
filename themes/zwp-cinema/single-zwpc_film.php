<?php get_header(); ?>
<main id="main" class="zwpc-film-page">
    <?php while (have_posts()) : the_post();
        $video = function_exists('zwpc_valid_video_url') ?
            zwpc_valid_video_url(get_post_meta(get_the_ID(), 'zwpc_video_url', true)) : '';
    ?>
        <p class="zwpc-eyebrow"><?php esc_html_e('NOW SHOWING · ZEA Z CINEMA', 'zwp-cinema'); ?></p>
        <h1><?php the_title(); ?></h1>
        <?php if ($video) : ?>
            <video class="zwpc-player" controls playsinline preload="metadata"
                <?php if (has_post_thumbnail()) : ?>
                    poster="<?php echo esc_url(get_the_post_thumbnail_url(get_the_ID(), 'large')); ?>"
                <?php endif; ?>>
                <source src="<?php echo esc_url($video); ?>"
                    type="<?php echo esc_attr(preg_match('/\\.webm(?:\\?|$)/i', $video) ? 'video/webm' : 'video/mp4'); ?>">
                <?php esc_html_e('Your browser cannot play this video.', 'zwp-cinema'); ?>
            </video>
        <?php elseif (has_post_thumbnail()) : ?>
            <?php the_post_thumbnail('large', array('class' => 'zwpc-poster')); ?>
        <?php endif; ?>
        <div class="entry-content"><?php the_content(); ?></div>
        <p><a class="zwpc-details-link" href="<?php echo esc_url(home_url('/')); ?>">
            <?php esc_html_e('← Back to the cinema', 'zwp-cinema'); ?></a></p>
        <?php if (comments_open() || get_comments_number()) : comments_template(); endif; ?>
    <?php endwhile; ?>
</main>
<?php get_footer(); ?>
