<?php
get_header();
$curauth = get_queried_object();
$bio = get_the_author_meta('zwpc_creator_bio', $curauth->ID);
$website = get_the_author_meta('zwpc_creator_website', $curauth->ID);
?>
<main id="primary" class="site-main">
    <header class="archive-header">
        <h1>Creator: <?php echo esc_html($curauth->display_name); ?></h1>
        <?php if ($bio): ?>
            <div class="creator-bio"><?php echo esc_html($bio); ?></div>
        <?php endif; ?>
        <?php if ($website): ?>
            <a href="<?php echo esc_url($website); ?>" class="creator-website"><?php echo esc_url($website); ?></a>
        <?php endif; ?>
    </header>
    <div class="creator-films">
        <?php
        $films = new WP_Query(array(
            'post_type' => 'zwpc_film',
            'author' => $curauth->ID,
            'posts_per_page' => 12,
        ));
        if ($films->have_posts()) : while ($films->have_posts()) : $films->the_post();
            $poster = get_the_post_thumbnail_url(get_the_ID(), 'medium');
        ?>
            <article class="film-card">
                <?php if ($poster): ?>
                    <img src="<?php echo esc_url($poster); ?>" alt="<?php the_title(); ?>" loading="lazy" />
                <?php endif; ?>
                <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            </article>
        <?php endwhile; endif; wp_reset_postdata(); ?>
    </div>
</main>
<?php get_footer(); ?>
