<form role="search" method="get" id="searchform" action="<?php echo esc_url(home_url('/')); ?>">
    <label for="s" class="screen-reader-text"><?php esc_html_e('Search for:', 'zwp-cinema'); ?></label>
    <input type="search" class="search-field" placeholder="<?php echo esc_attr__('Search films...', 'zwp-cinema'); ?>" value="<?php echo get_search_query(); ?>" name="s" id="s" />
    <input type="submit" class="search-submit" value="<?php echo esc_attr__('Search', 'zwp-cinema'); ?>" />
</form>
