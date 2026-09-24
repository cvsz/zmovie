<?php get_header();
$creator = get_queried_object();
?>
<main id="main" class="zwpc-film-page">
    <?php if ($creator instanceof WP_User) : ?>
        <p class="zwpc-eyebrow"><?php esc_html_e('CREATOR SPOTLIGHT', 'zwp-cinema'); ?></p>
        <h1><?php echo esc_html($creator->display_name); ?></h1>
        <p><?php echo esc_html(get_the_author_meta('description', $creator->ID)); ?></p>
        <?php
        $films = new WP_Query(array(
            'post_type' => 'zwpc_film',
            'post_status' => 'publish',
            'author' => $creator->ID,
            'posts_per_page' => 12,
            'paged' => max(1, (int) get_query_var('paged')),
        ));
        if ($films->have_posts()) :
            while ($films->have_posts()) : $films->the_post(); ?>
                <article>
                    <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                    <?php if (has_post_thumbnail()) : ?>
                        <a href="<?php the_permalink(); ?>"><?php the_post_thumbnail('medium', array('class' => 'zwpc-poster')); ?></a>
                    <?php endif; ?>
                    <p><?php echo esc_html(get_the_excerpt()); ?></p>
                </article>
            <?php endwhile;
            echo wp_kses_post(paginate_links(array(
                'total' => $films->max_num_pages, 'current' => max(1, (int) get_query_var('paged')),
            )));
            wp_reset_postdata();
        else : ?>
            <p><?php esc_html_e('No published films yet.', 'zwp-cinema'); ?></p>
        <?php endif; ?>
    <?php endif; ?>
</main>
<?php get_footer(); ?>
