<?php
/*
Template Name: My Favorites
*/
get_header();
?>
<main id="primary" class="site-main">
    <h1><?php esc_html_e('My Favorites', 'zwp-cinema'); ?></h1>
    <div id="favorites-list" class="film-grid">
        <!-- Favorites loaded via JS -->
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        fetch('<?php echo esc_url(rest_url('zwpc/v1/favorites')); ?>', { credentials: 'same-origin' })
            .then(r => r.json())
            .then(data => {
                const list = document.getElementById('favorites-list');
                if (data.favorites.length === 0) {
                    list.innerHTML = '<p>No favorites yet.</p>';
                    return;
                }
                list.innerHTML = data.favorites.map(f => `
                    <article class="film-card">
                        <img src="${f.poster_url}" alt="${f.title}" loading="lazy" />
                        <h2><a href="${f.permalink}">${f.title}</a></h2>
                    </article>
                `).join('');
            });
    });
    </script>
</main>
<?php get_footer(); ?>
