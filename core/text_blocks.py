"""The text_blocks module holds text blocks and colorization functions"""
from typing import Optional

def get_block(block_id: str) -> str:
    """Function returning the requested text_block"""
    return _text_blocks[block_id]

# supported ANSI foreground colors    
_fgcolors = {
    'black': '30',
    'red': '31',
    'green': '32',
    'yellow': '33',
    'blue': '34',
    'magenta': '35',
    'cyan': '36',
    'white': '37', 
}

# supported ANSI background colors
_bgcolors = {
    'black': '40',
    'red': '41',
    'green': '42',
    'yellow': '43',
    'blue': '44',
    'magenta': '45',
    'cyan': '46',
    'white': '47', 
}

def _reset() -> str:
    """Internal function returning ANSI escape sequence to reset all colors and boldness"""
    return '\033[0m'

def _bold() -> str:
    """Internal function returning ANSI escape sequence bolding foreground color"""
    return '\033[1m'

def _escfg(fg: str, bold: Optional[int] = False) -> str:
    """Internal function returning ANSI escape sequence setting foreground color with optional boldness"""
    if bold:
        sequence = ';'.join([str(int(bold)), _fgcolors[fg]])
    else:
        sequence = _fgcolors[fg]

    return f'\033[{sequence}m'

def _escbg(bg: str) -> str:
    """Internal function returning ANSI escape sequence setting background color"""
    return f'\033[{_bgcolors[bg]}m'

# text blocks with idenfier
_text_blocks = {
    '000000': f'\033[0;36m                                                          4888888p\n' \
              f'\033[0;36m                                  88888,                   88888\'\n' \
              f'\033[0;36m                                   8Oo88,                88888\'\n' \
              f'\033[0;36m                   88b           8888 8Oo8.      ,n.     8888\'\n' \
              f'\033[0;36m                  8O88b    7888 8   88 8Oo8.   48Oo88P ,888\'\n' \
              f'\033[0;36m                  4\033[1;36m8\033[0;37mOo8b    88 ,     88 8Oo8b    88o8\' 888\'\n' \
              f'\033[0;36m                   8\033[1;36m8\033[0;37mOo8b  88 ,8     888 8Oo88  888 88,88\'\n' \
              f'\033[0;36m                    8\033[1;36m8\033[0;37mOo8b 8\' 88b    88\'  88o8 888   888\'\n' \
              f'\033[0;36m                     8\033[1;36m8\033[1;37mo888\'   88b. 88\'     88888    88\'\n' \
              f'\033[0;36m                      487\'      8888\'      8888888  8888\n\n\n\n\n',
    '000001': f'{_escfg("cyan")}Enter account name or \'{_escfg("white", True)}c{_reset()}{_escfg("cyan")}\' to create: {_reset()}',
    '000002': f'{_escfg("cyan")}Password: {_reset()}',
    '000003': f'{_escfg("yellow")}\n-~=Creating New Account=~-{_escfg("cyan")}\nEnter new account name {_escfg("magenta")}(4 - 20 chars){_escfg("cyan")}: {_reset()}',
    '000004': f'{_escfg("cyan")}Enter your real name: {_reset()}',
    '000005': f'{_escfg("cyan")}Enter new password {_escfg("magenta")}(10 - 30 chars){_escfg("cyan")}: {_reset()}',
    '000006': f'{_escfg("cyan")}Re-enter password: {_reset()}',
    '000007': f'{_escfg("yellow")}\nAccount Created.  Returning to login prompt.\n\n{_reset()}',
    '000008': f'{_escfg("red")}Your account is already logged in... disconnecting\n\n{_reset()}',
    '000009': f'{_escfg("red")}\nIncorrect login or password\n\n{_reset()}',
    '000010': f'{_escfg("red")}\nExceeded maximum login attempts... disconnecting\n\n{_reset()}',
    '000011': f'{_escfg("red")}\nNot within character limit for account name {_escfg("magenta")}(4 - 20 chars){_escfg("red")}... try again\n\n{_reset()}',
    '000012': f'{_escfg("red")}\nAccount name cannot start with number or contain whitespace chars... please try again\n\n{_reset()}',
    '000013': f'{_escfg("red")}\nAccount name cannot contain ANSI escape sequences... please try again\n\n{_reset()}',
    '000014': f'{_escfg("red")}\nNot within character limit for password {_escfg("magenta")}(10 - 30 chars){_escfg("red")}... try again\n\n{_reset()}',
    '000015': f'{_escfg("red")}\nPassword cannot contain whitespace chars... please try again\n\n{_reset()}',
    '000016': f'{_escfg("red")}\nPasswords do not match... please try again\n\n{_reset()}',
    '000017': f'{_escfg("red")}\nAccount name already in use... please choose another\n\n{_reset()}'
}




