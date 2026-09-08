class ZMovieError(RuntimeError):
    """Base production-platform error."""


class NotFoundError(ZMovieError):
    pass


class RenderError(ZMovieError):
    pass
