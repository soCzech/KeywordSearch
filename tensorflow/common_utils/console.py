import os


class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})): pass


class ProgressTracker(Singleton):

    def __init__(self):
        self._current = 0
        self._total = 0
        self._digits = 0

    def reset(self, total):
        self._current = 0
        self._total = total
        self._digits = len(str(total))

        self._calculate_bar_width()
        self._draw()

    def _calculate_bar_width(self):
        (self._tw, self._th) = ProgressTracker._terminal_size()
        self._bar_width = self._tw - (2 * self._digits + 3 + 5)

    def _draw(self):
        if self._total == 0:
            return
        self._clear()

        print("%-*s%3d%% (%*d/%*d)" % (
            self._bar_width,
            "=" * round(self._bar_width * self._current / self._total),
            round(self._current / self._total * 100),
            self._digits,
            self._current,
            self._digits,
            self._total
        ), end='\r')

    def _clear(self):
        self._calculate_bar_width()
        # sys.stdout.write("\033[K")
        # to fix bug when logging to console
        print(" " * self._tw, end='\r')
        # sys.stdout.write("\033[K")

    def set_progress(self, current):
        self._current = current
        self._draw()
        if self._current == self._total:
            self.reset(0)

    def increment(self):
        self.set_progress(self._current + 1)

    def info(self, message):
        self._clear()
        print(message)
        self._draw()

    # http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    @staticmethod
    def _terminal_size():
        env = os.environ

        def ioctl_GWINSZ(fd):
            try:
                import fcntl, termios, struct
                cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            except:
                return
            return cr

        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
        if not cr:
            cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
        return int(cr[1]), int(cr[0])
