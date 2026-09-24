# Nginx Cinema symlink

`/var/www/cinema` is a symlink to `/var/www/zmovie-cinema` so the
`root /var/www` + `try_files` routing resolves `/cinema/index.php`
correctly. See `deploy/nginx/zmovie-cinema.conf.example`.
