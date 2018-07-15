import os
import datetime
import math


class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass


class ProgressTracker(Singleton):
    """
    A class tracking progress and showing a progress bar.
    """

    def __init__(self):
        self._current = 0
        self._total = 0
        self._digits = 0

        self._remaining_time = "?"
        self._last_current = 0
        self._last_time = None

    def reset(self, total):
        """Resets current count and sets new number of steps.

        Args:
            total: Number of steps to end.
        """
        self._current = 0
        self._total = total
        self._digits = len(str(total))

        self._remaining_time = "?"
        self._last_current = 0
        self._last_time = None

        self._calculate_bar_width()
        self._draw()

    def _calculate_bar_width(self):
        """
        Calculates width of a progress bar.
        """
        (self._tw, self._th) = ProgressTracker._terminal_size()
        self._bar_width = self._tw - (2 * self._digits + 3 + 5 + 5 + len(self._remaining_time))

    def _draw(self):
        """
        Draws a progress bar if there are still some steps to perform.
        """
        if self._total == 0:
            return
        self._clear()

        print('{0:-<{1}}{2:3d}% ({3:{5}d}/{4:{5}d}) ETA {6}'.format(
            "=" * round(self._bar_width * self._current / self._total),
            self._bar_width,
            round(math.floor(self._current / self._total * 100)),
            self._current,
            self._total,
            self._digits,
            self._remaining_time
        ), end='\r')

    def _clear(self):
        """
        Clears the current line in console.
        """
        self._calculate_bar_width()
        # sys.stdout.write("\033[K")
        # to fix bug when logging to console
        print(" " * self._tw, end='\r')
        # sys.stdout.write("\033[K")

    def set_progress(self, current):
        """Sets current status of progress bar to a defined number of steps.

        Args:
            current: The current step number.
        """
        self._current = current
        if self._last_time is None or (datetime.datetime.now() - self._last_time).seconds > 1:
            self._update_time()

        self._draw()
        if self._current == self._total:
            self.reset(0)

    def _update_time(self, current=None, total=None):
        """Updates time to the end based on duration of previous iteration.

        Args:
            current: The current step.
            total: The total number of steps.
        """
        if current is None:
            current = self._current
        if total is None:
            total = self._total

        if self._last_time is None:
            self._last_time = datetime.datetime.now()
            self._remaining_time = "?"
        else:
            diff = datetime.datetime.now() - self._last_time
            self._last_time = datetime.datetime.now()
            diff = (diff.seconds * 1E6 + diff.microseconds) /\
                   (current - self._last_current) * (total - current) / 1E6
            self._last_current = current

            if diff > 3600:
                h = round(diff//3600)
                m = round((diff - h*3600)/60)
                self._remaining_time = "{0:d}h {1:d}m".format(int(h), int(m))
            elif diff > 60:
                m = round(diff // 60)
                s = round((diff - m * 60))
                self._remaining_time = "{0:d}m {1:d}s".format(int(m), int(s))
            else:
                self._remaining_time = "{0:d}s".format(int(round(diff)))

    def increment(self, val=1):
        """Increments number of steps.

        Args:
            val: The number of steps to increment the counter by.
        """
        self.set_progress(self._current + val)

    def info(self, message):
        """Print a message on separate line.

        Args:
            message: A message to print.
        """
        self._clear()
        print(message)
        self._draw()

    def progress_info(self, message, params, current=None, total=None):
        """Instead of progress bar, only message can be showed.

        Args:
            message: The message to show.
            params: If any params should be substituted into the message using pythons string.format().
            current: The current step.
            total: The total number of steps.
        """
        self._clear()
        if current is not None and total is not None:
            if self._last_time is None or (datetime.datetime.now() - self._last_time).seconds > 1:
                self._update_time(current, total)

        print(message.format(*params) + " ETA {}".format(self._remaining_time), end="\r")

    def error(self, message):
        """Print message with 'ERROR' at the beginning of a line.

        Args:
            message: The message to print.
        """
        self._clear()
        print("ERROR:", message)
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
