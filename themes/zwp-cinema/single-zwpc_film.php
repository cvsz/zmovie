<?php
get_header();
$film = get_post();
$video_url = get_post_meta($film->ID, 'zwpc_video_url', true);
$poster_url = get_post_meta($film->ID, 'zwpc_poster_url', true) ?: get_the_post_thumbnail_url($film->ID, 'large');
$runtime = get_post_meta($film->ID, 'zwpc_runtime', true);
$age_rating = get_post_meta($film->ID, 'zwpc_age_rating', true);
$genres = wp_get_post_terms($film->ID, 'zwpc_genre', array('fields' => 'names'));
$creator = get_post_meta($film->ID, 'zwpc_creator', true) ?: get_the_author();
?>
<main id="primary" class="site-main">
    <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
        <header class="entry-header">
            <?php if ($poster_url): ?>
                <img src="<?php echo esc_url($poster_url); ?>" alt="<?php the_title(); ?>" class="film-poster" loading="lazy" />
            <?php endif; ?>
            <h1 class="entry-title"><?php the_title(); ?></h1>
        </header>
        <div class="entry-content">
            <?php if (!empty($genres)): ?>
                <span class="film-genres"><?php echo esc_html(implode(', ', $genres)); ?></span>
            <?php endif; ?>
            <?php if ($runtime): ?>
                <span class="film-runtime"><?php echo esc_html($runtime); ?> min</span>
            <?php endif; ?>
            <?php if ($age_rating): ?>
                <span class="film-age-rating"><?php echo esc_html($age_rating); ?></span>
            <?php endif; ?>
            <div class="film-creator"><?php echo esc_html($creator); ?></div>
            <?php the_content(); ?>
            <?php if ($video_url): ?>
                <div class="film-player">
                    <video controls preload="metadata" poster="<?php echo esc_url($poster_url); ?>">
                        <source src="<?php echo esc_url($video_url); ?>" type="video/mp4" />
                    </video>
                </div>
            <?php endif; ?>
        </div>
    </article>
</main>
<?php get_footer(); ?>
