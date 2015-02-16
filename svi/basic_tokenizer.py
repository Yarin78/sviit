import logging
from disk import Disk

def read_word(bytes, pos):
    return bytes[pos] + bytes[pos+1] * 256

def read_float(bytes):
    num = 0
    for b in bytes[1:]:
        num = num * 10 + b / 16
        num = num * 10 + b % 16
    while num >= 1:
        num /= 10.0
    num = num * 10 ** (bytes[0] - 0x40)
    return num

def format_float(num):
    return "%.14g" % num

def detokenize(bytes):
    if type(bytes) is str:
        bytes = [ord(x) for x in bytes]
    lines = []
    pos = 0
    while True:
        if pos + 2 > len(bytes):
            logging.warning("Program ended abruptly")
            break
        next_row = read_word(bytes, pos)
        if next_row == 0:
            # TODO: Warn if remaining bytes
            break
        next_row -= 32769  # Program is loaded into 0x8001
        if next_row < pos+4:
            lines.append("*** UNEXPECTED EOF")
            logging.warning("Invalid line pointer, aborting tokenizing")
            break
        lines.append(detokenize_line(bytes[pos+2:next_row]))
        pos = next_row
    return lines

def detokenize_line(bytes):
    if len(bytes) < 2:
        logging.warning("Line less than two bytes, skipping")
        return "*** UNEXPECTED EOL"
    line_number = read_word(bytes, 0)
    #print ["%02x" % x for x in bytes]

    line = '%d ' % line_number
    pos = 2
    while pos < len(bytes) and bytes[pos] != 0:
        token = bytes[pos]
        pos += 1
        if token >= 32 and token < 127:
            line += chr(token)
        elif token == 12:
            line += "&H%X" % read_word(bytes, pos)
            pos += 2
        elif token == 14:
            # Same as 28!?
            # Positive numebr?
            line += "%d" % read_word(bytes, pos)
            pos += 2
        elif token == 15:
            line += "%d" % bytes[pos]
            pos += 1
        elif token >= 17 and token < 27:
            line += "%d" % (token - 17)
        elif token == 28:
            # Same as 14!?
            # Negative number? (but minus sign is still explicit before)
            line += "%d" % read_word(bytes, pos)
            pos += 2
        elif token == 29:
            line += "%s!" % format_float(read_float(bytes[pos:pos+4]))
            pos += 4
        elif token == 31:
            line += "%s#" % format_float(read_float(bytes[pos:pos+8]))
            pos += 8
        elif token < 32:
            raise Exception("Unknown token %d on line number %d" % (bytes[pos], line_number))
        else:
            # TODO: Graphical characters!
            if token == 255:
                token = bytes[pos] % 128
                pos += 1
            if token == 0xe6:
                # When using apostroph as comments, it's encoded :REM'
                # We nee to remove the previous four characters to get same decoding
                # TODO: THere's something more to this. The rest of the characters are never tokens?
                line = "%s'" % line[:-4]
            else:
                s = TOKENS[token]
                if len(s) == 0:
                    raise Exception("Unknown token %d on line number %d" % (token, line_number))
                else:
                    line += TOKENS[token]

    if pos >= len(bytes):
        line += " *** BUFFER ENDED PREMATURELY"
        logging.warning("Buffer ended before EOL token on line number %d" % line_number)
    elif pos + 1 != len(bytes):
        line += " *** GOT EOL BUT BUFFER NOT EMPTY"
        logging.warning("Got EOL token on line number %d but not end of buffer" % line_number)

    #print line
    return line

TOKENS = [
    '', 'LEFT$', 'RIGHT$', 'MID$', 'SGN', 'INT', 'ABS', 'SQR', 'RND', 'SIN', 'LOG', 'EXP', 'COS', 'TAN', 'ATN', 'FRE',
    'INP', 'POSE', 'LEN', 'STR$', 'VAL', 'ASC', 'CHR$', 'PEEK', 'VPEEK', 'SPACE$', 'OCT$', 'HEX$', 'LPOS', 'BIN$', 'CINT', 'CSNG',
    'CDBL', 'FIX', 'STICK', 'STRIG', 'PDL', 'PAD', 'DSKF', 'FPOS', 'CVI', 'CVS', 'CVD', 'EOF', 'LOC', 'LOF', 'MKI$', 'MKS$',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    'MKD$', 'END', 'FOR', 'NEXT', 'DATA', 'INPUT', 'DIM', 'READ', 'LET', 'GOTO', 'RUN', 'IF', 'RESTORE', 'GOSUB', 'RETURN', 'REM',
    'STOP', 'PRINT', 'CLEAR', 'LIST', 'NEW', 'ON', 'WAIT', 'DEF', 'POKE', 'CONT', 'CSAVE', 'CLOAD', 'OUT', 'LPRINT', 'LLIST', 'CLS',
    'WIDTH', 'ELSE', 'TRON', 'TROFF', 'SWAP', 'ERASE', 'ERROR', 'RESUME', 'DELETE', 'AUTO', 'RENUM', 'DEFSTR', 'DEFINT', 'DEGSNG', 'DEFDBL', 'LINE',
    'OPEN', 'FIELD', 'GET', 'PUT', 'CLOSE', 'LOAD', 'MERGE', 'FILES', 'LSET', 'RSET', 'SAVE', 'LFILES', 'CIRCLE', 'COLOR', 'DRAW', 'PAINT',
    'BEEP', 'PLAY', 'SET', 'PRESET', 'SOUND', 'SCREEN', 'VPOKE', 'KEY', 'CLICK', 'SWITCH', 'MAX', 'MON', 'MOTO', 'BLOAD', 'BSAVE', 'MDM',
    'DIAL', 'DKSO$', 'SET', 'NAME', 'KILL', 'IPL', 'COPY', 'CMD', 'LOCATE', 'TO', 'THEN', 'TAB(', 'STEP', 'USR', 'FN', 'SPC(',
    'NOT', 'ERL', 'ERR', 'STRING$', 'USING', 'INSTR', '', 'VARPTR', 'CSRLIN', 'ATTR$', 'DSKI$', 'OFF', 'INKEY$', 'POINT', 'SPRITE', 'TIME',
    '>', '=', '<', '+', '-', '*', '/', '^', 'AND', 'OR', 'XOR', 'EQV', 'IMP', 'MOD', '\\', ''
]

def main():
    disk = Disk('/Users/yarin/Dropbox/SVI/Disk/tokentest.dsk')
    data = disk.read_file('rem')
    lines = detokenize(data)
    for line in lines:
        print line

if __name__ == "__main__":
    main()
