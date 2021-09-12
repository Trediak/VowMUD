async def get_template(type: str, template_name: str):
    type = type.lower()

    if type in ['chat', 'system']:
        if type == 'chat':
            if template_name in _template_chat:
                return _template_chat[template_name]
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
_template_system = {
    'invalid_command': '\033[31m\'%s\' is not a valid command.\033[0m\n',
    'not_logged_in': '\033[31mUser \'%s\' is not currently logged in.\033[0m\n',
}
_template_chat = {
    'gossip': '\033[1;35m%s \033[0;35mgossip%s: %s\033[0m\n',
    'tell': '\033[1;36m%s \033[0;36mtell%s %s: %s\033[0m\n',
}