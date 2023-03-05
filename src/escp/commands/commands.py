from typing import Self
from abc import ABC

from .parameters import Margin, PageLengthUnit, Typeface, Justification


def int_to_bytes(value: int) -> bytes:
    return int.to_bytes(value, length=1, byteorder='big', signed=False)


class Commands(ABC):

    cmds = {
        'init': b'\x1b@',
        'cr_lf': b'\x0d\x0a',
        'character_width_10': b'\x1bP',
        'character_width_12': b'\x1bM',
        'character_width_15': b'\x1bg',
        'bold_on': b'\x1bE',
        'bold_off': b'\x1bF',
        'italic_on': b'\x1b4',
        'italic_off': b'\x1b5',
        'double_strike_on': b'\x1bG',
        'double_strike_off': b'\x1bH',
        'typeface': b'\x1bk',
        'margin_left': b'\x1bl',
        'margin_right': b'\x1bQ',
        'margin_bottom': b'\x1b2',  # FIXME autogenerated
        'page_length_in_lines': b'\x1bC',
        'page_length_in_inches': b'\x1bC\x00',
        'double_character_width': b'\x1bW',
        'double_character_height': b'\x1bw',
        'extra_space': b'\x1b ',
        'condensed_on': b'\x1b\x0f',
        'condensed_off': b'\x1b\x12',
        'line_spacing_1_6': b'\x1b2',
        'line_spacing_1_8': b'\x1b0',
        'proportional': b'\x1bp',
        'justify': b'\x1ba',
        'form_feed': b'\x0c',
    }

    _buffer: bytes

    def __init__(self):
        self.clear()

    def _commands(self):
        return self.cmds

    def init(self) -> Self:
        return self._append_cmd('init')

    def draft(self, enabled: bool) -> Self:
        return self

    def text(self, content: bytes | str) -> Self:
        if isinstance(content, str):
            content = bytes(content, 'utf-8')
        return self._append(content)

    def cr_lf(self, how_many=1) -> Self:
        return self._append(self._commands()['cr_lf'] * how_many)

    def bold(self, enabled: bool) -> Self:
        return self._append_cmd('bold_on' if enabled else 'bold_off')

    def italic(self, enabled: bool) -> Self:
        return self._append_cmd('italic_on' if enabled else 'italic_off')

    def double_strike(self, enabled: bool) -> Self:
        """Prints each dot twice, with the second slightly below the first, creating bolder characters."""
        return self._append_cmd('double_strike_on' if enabled else 'double_strike_off')

    def character_width(self, width: int) -> Self:
        """Select the character width. This may set the point as well.

        :param width: 10, 12 or 15.
        On non- 9-pin printers, the point is set to 10.5 as well.
        """
        if width not in (10, 12, 15):
            raise ValueError(f'Invalid char width: ${width}')
        return self._append_cmd(f'character_width_{width}')

    def typeface(self, tf: Typeface) -> Self:
        return self._append_cmd('typeface', int_to_bytes(tf.value))

    def margin(self, margin: Margin, value: int) -> Self:
        """Set a margin.

        The right margin value starts from the left margin.
        Example:
            left margin = 10 (1 inch left margin)
            right margin = 75 (1 inch right margin)

        Top margin is only available on ESC/P2 printers.

        Bottom margin on non ESC/P2 is only available with continuous paper.
        """
        if value < 0 or value > 255:
            raise ValueError(f'Invalid margin value: ${value}')
        return self._append_cmd(f'margin_{margin.name.lower()}', int_to_bytes(value))

    def line_spacing(self, numerator: int, denominator: int) -> Self:
        """Set line spacing.

        Changing the line spacing after the page length does not affect the page length.
        Always set the line spacing before the page length.
        """
        raise NotImplementedError()

    def page_length(self, value: int, unit: PageLengthUnit) -> Self:
        """Set page length.

        Always set the line spacing before the page length.
        Always set the page length before the paper is loaded
        or when the print position is at the top of the page.
        Setting the page length cancels the bottom margin.

        :param value The number of lines per page
        :param unit The unit of the page length
        """
        cmd = 'page_length_in_inches' if unit == PageLengthUnit.INCHES else 'page_length_in_lines'
        return self._append_cmd(cmd, bytes(value))

    def double_character_width(self, enabled: bool) -> Self:
        return self._append_cmd('double_character_width', int_to_bytes(1) if enabled else int_to_bytes(0))

    def double_character_height(self, enabled: bool) -> Self:
        return self._append_cmd('double_character_height', int_to_bytes(1) if enabled else int_to_bytes(0))

    def extra_space(self, value: int) -> Self:
        """Add extra space between characters.

        The fraction of inch depends on the number of pins.
        """
        if value < 0 or value > 255:
            raise ValueError(f'Invalid extra space value: ${value}')
        return self._append_cmd('extra_space', int_to_bytes(value))

    def condensed(self, enabled: bool) -> Self:
        """Select condensed printing.

        1/17 inch if 10-cpi selected,
        1/20 inch if 12-cpi selected
        """
        return self._append_cmd('condensed_on' if enabled else 'condensed_off')

    def proportional(self, enabled: bool) -> Self:
        """Select proportional printing.

        - Changes made to fixed-pitch printing are not effective until proportional printing is turned off.
        - Condensed printing is not effective when proportional printing is turned on.

        Printers not featuring this command:
        ActionPrinter Apex 80, ActionPrinter T-1000, ActionPrinter 2000, LX-400, LX-800, LX-810,
        LX-850, LX-1050
        """
        return self._append_cmd('proportional', int_to_bytes(1) if enabled else int_to_bytes(0))

    def justify(self, justification: Justification) -> Self:
        """Set justification.

        - This is a non-recommended command as per Epson documentation,
          although no explanation is given.
        - Always set justification at the beginning of a line.
        - The printer performs full justification only if the width of the current line is greater than
          75% of the printing area width. If the line width is less than 75%, the printer left-justifies text.
        - You should not use commands that adjust the horizontal print position during full justification.
        - Justification is based on the font selected when the justification command is sent.
          Changing the font after setting justification can cause unpredictable results.
        """
        return self._append_cmd('justify', int_to_bytes(justification.value))

    def form_feed(self) -> Self:
        return self._append_cmd('form_feed')

    def _append(self, b: bytes) -> Self:
        self._buffer += b
        return self

    def _append_cmd(self, cmd: str, param: bytes = None) -> Self:
        seq = self._commands()[cmd]
        if not seq:
            raise RuntimeError(f'No sequence found for {cmd}')
        if param:
            seq += param
        return self._append(seq)

    def clear(self) -> Self:
        self._buffer = b''
        return self

    @property
    def buffer(self) -> bytes:
        return self._buffer
