import logging

class ColorFormatter(logging.Formatter):
    LEVEL_STYLES = {
        'DEBUG': '\033[97;46m',
        'INFO': '\033[97;42m',
        'WARNING': '\033[97;43m',
        'ERROR': '\033[97;41m',
        'CRITICAL': '\033[97;45m',
    }
    RESET = '\033[0m'
    TIMESTAMP = '\033[35;45m'

    def format(self, record):
        level_color = self.LEVEL_STYLES.get(record.levelname, '')
        timestamp = f"{self.TIMESTAMP}[{self.formatTime(record, datefmt='%Y-%m-%d %H:%M:%S')}]{self.RESET}"
        message = super().format(record)
        return f"{timestamp} {level_color}{record.levelname}{self.RESET} - {record.getMessage()}"