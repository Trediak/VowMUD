async def get_template(type: str, template_name: str):
    type = type.lower()

    if type in ['chat', 'game', 'system']:
        if type == 'chat':
            if template_name in _template_chat:
                return _template_chat[template_name]
            else:
                # TODO: make this an exception
                print('Error: not a valid template name')
        if type == 'game':
            if template_name in _template_game:
                return _template_game[template_name]
            else:
                # TODO: make this an exception
                print('Error: not a valid template name')
        if type == 'system':
            if template_name in _template_system:
                return _template_system[template_name]
            else:
                # TODO: make this an exception
                print('Error: not a valid template name')
    else:
        # TODO: make this an exception
        print('Error: not a valid template type')

# supported ANSI codes
# reset   = 0
# bright  = 1

# supported ANSI foreground colors    
# black   = 30
# red     = 31
# green   = 32
# yellow  = 33
# blue    = 34
# magenta = 35
# cyan    = 36
# white   = 37

# supported ANSI background colors
# black   = 40
# red     = 41
# green   = 42
# yellow  = 43
# blue    = 44
# magenta = 45
# cyan    = 46
# white   = 47

_template_system = {
    # substitutions: command name
    'invalid_command': '\033[31m\'%s\' is not a valid command.\033[0m\n',
    # substitutions: user name
    'not_logged_in': '\033[31mUser \'%s\' is not currently logged in.\033[0m\n',
}

_template_game = {
    # substitutions: room name, room description, exits text, npc's in room
    'room': '\033[1;36m%s\n\033[0;37m%s\n\n\033[0;32mApparent exits: \033[1;35m%s\n\033[0;32mAlso here: \033[1;31m%s\n',
    # substitutions: direction + excess
    'invalid_direction': '\033[0;31m"%s" is not a valid direction',
    # substitutions: None
    'no_exit': '\033[0;31mNo exit in that direction'
}

_template_chat = {
    # substitutions: source user name or 'You', empty or 's', message
    'gossip': '\033[1;35m%s \033[0;35mgossip%s: %s\033[0m\n',
    # substitutions: source user name or 'You', empty or 's', destination user name or 'you', message
    'tell': '\033[1;36m%s \033[0;36mtell%s %s: %s\033[0m\n',
}