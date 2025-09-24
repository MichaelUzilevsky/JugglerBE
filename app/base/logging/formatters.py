import logging
from collections import OrderedDict

from pythonjsonlogger.json import JsonFormatter


class NoExcConsoleFormatter(logging.Formatter):
    """Console formatter that ignores traceback text."""

    def formatException(self, ei):
        return ""


class CustomJsonFormatter(JsonFormatter):
    """
    Json formatter that:
      - ensures 'timestamp' key instead of 'asctime'
      - ensures 'exc_text' contains the traceback when exc_info is present (else null)
      - leaves other `extra` keys (from record.__dict__) intact
    """

    def add_fields(self, log_record, record, message_dict):
        # First collect fields using parent logic
        super().add_fields(log_record, record, message_dict)

        ordered = OrderedDict()

        if "asctime" in log_record:
            ordered["timestamp"] = log_record.pop("asctime")
        else:
            ordered["timestamp"] = self.formatTime(record, self.datefmt)

        # copy everything else except exc_text (we’ll handle it manually)
        for key, value in log_record.items():
            if key != "exc_text":
                ordered[key] = value

        # Add exc_text only if record.exc_info exists
        if record.exc_info:
            ordered["exc_text"] = self.formatException(record.exc_info)

        # Replace log_record contents with ordered dict
        log_record.clear()
        log_record.update(ordered)
