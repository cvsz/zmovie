<?php get_header(); ?>
<main id="main" class="zwpc-main">
    <div class="zwpc-intro">
        <p class="zwpc-eyebrow"><?php esc_html_e('THE CINEMA EXPERIENCE', 'zwp-cinema'); ?></p>
        <h1><?php esc_html_e('Every story deserves a screen.', 'zwp-cinema'); ?></h1>
        <p><?php esc_html_e('Explore independently curated films, trailers and stories in a cinematic vertical feed.', 'zwp-cinema'); ?></p>
    </div>
    <?php if (post_type_exists('zwpc_film')) :
        $selected_genre = isset($_GET['genre']) && is_string($_GET['genre'])
            ? sanitize_title(wp_unslash($_GET['genre'])) : '';
        $terms = get_terms(array('taxonomy' => 'zwpc_genre', 'hide_empty' => true));
    ?>
        <div class="zwpc-toolbar">
            <label for="zwpc-genre"><?php esc_html_e('Explore by genre', 'zwp-cinema'); ?></label>
            <select id="zwpc-genre">
                <option value=""><?php esc_html_e('All genres', 'zwp-cinema'); ?></option>
                <?php if (!is_wp_error($terms)) : foreach ($terms as $term) : ?>
                    <option value="<?php echo esc_attr($term->slug); ?>" <?php selected($selected_genre, $term->slug); ?>>
                        <?php echo esc_html($term->name); ?>
                    </option>
                <?php endforeach; endif; ?>
            </select>
            <span class="zwpc-toolbar-hint"><?php esc_html_e('Swipe · Scroll · Arrow keys', 'zwp-cinema'); ?></span>
        </div>
        <?php
        $args = array('post_type' => 'zwpc_film', 'post_status' => 'publish',
            'posts_per_page' => 6, 'paged' => 1, 'orderby' => 'date', 'order' => 'DESC');
        if ($selected_genre) {
            $args['tax_query'] = array(array('taxonomy' => 'zwpc_genre', 'field' => 'slug', 'terms' => $selected_genre));
        }
        $films = new WP_Query($args);
        ?>
        <div id="zwpc-feed" class="zwpc-feed" aria-label="<?php esc_attr_e('Cinema film feed', 'zwp-cinema'); ?>"
            data-next-page="2" data-has-more="<?php echo $films->max_num_pages > 1 ? '1' : '0'; ?>">
            <?php while ($films->have_posts()) : $films->the_post();
                $item = function_exists('zwpc_film_data') ? zwpc_film_data(get_the_ID()) : null;
                if (!$item) { continue; }
            ?>
                <article class="zwpc-reel" tabindex="0" data-film-id="<?php echo esc_attr($item['id']); ?>">
                    <div class="zwpc-reel-media">
                        <?php if ($item['video']) : ?>
                            <video playsinline muted preload="none" loop <?php if ($item['poster']) : ?>
                                poster="<?php echo esc_url($item['poster']); ?>"<?php endif; ?>>
                                <source src="<?php echo esc_url($item['video']); ?>" type="<?php echo esc_attr(preg_match('/\\.webm(?:\\?|$)/i', $item['video']) ? 'video/webm' : 'video/mp4'); ?>">
                            </video>
                        <?php elseif ($item['poster']) : ?>
                            <img loading="lazy" src="<?php echo esc_url($item['poster']); ?>"
                                alt="<?php echo esc_attr($item['title']); ?>">
                        <?php endif; ?>
                        <div class="zwpc-shade"></div>
                    </div>
                    <div class="zwpc-reel-text">
                        <p class="zwpc-eyebrow"><?php echo esc_html(implode(' / ', $item['genres'])); ?></p>
                        <h2><a href="<?php echo esc_url($item['url']); ?>"><?php echo esc_html($item['title']); ?></a></h2>
                        <p><?php echo esc_html(wp_trim_words($item['excerpt'], 24)); ?></p>
                        <span><?php echo esc_html($item['creator']); ?></span>
                        <a class="zwpc-details-link" href="<?php echo esc_url($item['url']); ?>"><?php esc_html_e('View film details ↗', 'zwp-cinema'); ?></a>
                    </div>
                    <div class="zwpc-reel-actions">
                        <button class="zwpc-play" type="button" aria-label="<?php esc_attr_e('Play or pause trailer', 'zwp-cinema'); ?>">▶</button>
                        <button class="zwpc-favorite" type="button" aria-pressed="false"
                            aria-label="<?php esc_attr_e('Save to favorites', 'zwp-cinema'); ?>">♡</button>
                    </div>
                </article>
            <?php endwhile; wp_reset_postdata(); ?>
        </div>
        <p id="zwpc-status" class="zwpc-status" role="status" aria-live="polite"><?php if ((int) $films->post_count === 0) {
            esc_html_e('No films yet. Publish your first film from Cinema Films in WordPress.', 'zwp-cinema');
        } ?></p>
        <div id="zwpc-sentinel" aria-hidden="true"></div>
        <div class="zwpc-nav-controls">
            <button id="zwpc-prev" type="button" aria-label="<?php esc_attr_e('Previous film', 'zwp-cinema'); ?>">↑</button>
            <button id="zwpc-next" type="button" aria-label="<?php esc_attr_e('Next film', 'zwp-cinema'); ?>">↓</button>
        </div>
    <?php else : ?>
        <section class="zwpc-empty">
            <h2><?php esc_html_e('The cinema is being prepared.', 'zwp-cinema'); ?></h2>
            <p><?php esc_html_e('Activate the first-party ZeaZ Cinema plugin to start curating films.', 'zwp-cinema'); ?></p>
            <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
                <h3><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
            <?php endwhile; endif; ?>
        </section>
    <?php endif; ?>
</main>
<?php get_footer(); ?>
