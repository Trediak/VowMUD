"""Module containing authorization related classes and functions

Contained classes either directly control or assist in the control of authorization
of user login and account creation or other authorization activities over the user's
connection lifetime.

routine listings
----------------
AuthStateMachine
    Process of user authorization, and account creation if no account exists for user, is
    handled entirely by this state machine.  The user transitions between states based on
    prompt responses, validation, and connection integrity.

    States transitions, and optionally executed function, are setup via a class method to
    keep things tidy and within the state machine.  Called funtions must include async
    in the definition and should be defined as private outside of the state machine.

    Extension of the state machine should be as easy as adding a new transition and called
    function.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
import re
import bcrypt
from core.database import query_table, insert_user_account
from core.managers.logger_manager import logger_manager
from core.managers.manager_hub import manager_hub
from core.text_blocks import get_block

if TYPE_CHECKING:
    from asyncio.streams import StreamReader
    from core.user import User

@dataclass
class SimpleAuth():
    """Class to store information during login process.

    Attributes
    ----------
    account_name : str
        Account name entered during login process
    password : str
        Password entered during login process

    Methods
    -------
    None

    """
    account_name: str = ''
    password: str = ''

@dataclass
class AccountCreation():
    """Class to store information during account creation process.

    Attributes
    ----------
    account_name : str
        Account name entered during account creation process
    password : str
        Password entered during account creation process
    real_name : str
        Real name entered during account creation process

    Methods
    -------
    None

    """
    account_name: str = ''
    password: str = ''
    real_name: str = ''

class UserAuthPackage():
    """Class to store authorization information during authorization process.

    Attributes
    ----------
    input_reader : asyncio.StreamReader
        StreamReader associated with user for gathering input
    input_tracker : SimpleAuth or AccountCreation
        Instance of class to store information specific to users choice of login or account creation
    user_object : User
        Instance of User associated with user in authorization process
    user_login_attempts: int
        User's current number of attempts logging in, by default 0.

    Methods
    -------
    None

    """
    def __init__(self, user_object: User, reader: StreamReader) -> None:
        self.input_reader = reader
        self.input_tracker = None
        self.user_object = user_object
        self.user_login_attempts = 0

class AuthStateMachine():
    """State machine which manages login authentication and account creation states and transitions.

    Attributes
    ----------
    handlers : dict[str, Callable]
        Dictionary of transition names, as str, and associated state function
    end_states : list[str]
        List of transitions names with end_state set as True
    start_state : str
        The transition string designated as the entrance transition in state machine

    Methods
    -------
    setup()
        Set up state machine transitions, starting state, and end states
    add_state(name: str, handler, end_state: bool = False)
        Add new state to state machine
    run(user_pkg: UserAuthPackage)
        Run state machine from start_state

    """
    def __init__(self) -> None:
        self.handlers = {}
        self.end_states = []
        self.start_state = None

    def setup(self) -> None:
        """This function sets up state machine transitions, starting state, and end states
        """
        self.add_state('auth_initial_state', _state_login_title)                                    # general
        self.add_state('displayed_login_title', _state_login_prompt)                                # general
        self.add_state('prompted_for_login', _state_login_process)                                  # authorization
        self.add_state('login_processed', _state_password_prompt)                                   # authorization
        self.add_state('prompted_for_password', _state_password_process)                            # authorization
        self.add_state('password_processed', _state_validate)                                       # authorization
        self.add_state('validated', _state_authorized)                                              # authorization
        self.add_state('authorized', None, end_state=True)                                          # authorization
        self.add_state('create_initial_state', _state_new_account_prompt)                           # account creation
        self.add_state('prompted_for_new_account_name', _state_new_account_process)                 # account creation
        self.add_state('new_account_name_processed', _state_real_name_prompt)                       # account creation
        self.add_state('prompted_for_real_name', _state_real_name_process)                          # account creation
        self.add_state('real_name_processed', _state_new_password_prompt)                           # account creation
        self.add_state('prompted_for_new_password', _state_new_password_process)                    # account creation
        self.add_state('new_password_processed', _state_reenter_new_password_prompt)                # account creation
        self.add_state('prompted_for_reenter_new_password', _state_reenter_new_password_process)    # account creation
        self.add_state('reenter_new_password_processed', _state_create_new_account)                 # account creation
        self.add_state('new_account_created', _state_inform_of_login)                               # account creation
        self.add_state('error_state', _state_error, end_state=True)                                 # general
        self.set_start('auth_initial_state')

    def add_state(self, name: str, handler, end_state: bool = False) -> None:
        """This function adds a new state to the state machine.

        Parameters
        ----------
        name : str
            Transition name
        handler : Callable
            Function name to be executed on transition
        end_state : bool, optional
            True if state is an end state else False, by default False

        Returns
        -------
        None
        """
        self.handlers[name] = handler

        if end_state:
            self.end_states.append(name)

    def set_start(self, name: str) -> None:
        """This function sets the start function for state machine.

        Parameters
        ----------
        name : str
            Transition string to be set as initial transition for state machine.

        Returns
        -------
        None
        """
        self.start_state = name

    async def run(self, user_pkg: UserAuthPackage) -> None:
        """This function executes the state machine starting at the state set in set_start.

        Parameters
        ----------
        user_pkg : UserAuthPackage
            Instance of UserAuthPackage which stores authorization information during authorization process

        Returns
        -------
        None
        """
        handler = self.handlers[self.start_state]

        while True:
            (new_state, user_pkg) = (await handler(user_pkg))

            if new_state in self.end_states:
                break

            handler = self.handlers[new_state]

async def _state_login_title(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends login title to the user's connection.

    Transition(s):
        'displayed_login_title' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000000').encode('ascii'))
    await user_pkg.user_object.socket.drain()

    await logger_manager.authorization.info(
        {
            'type': 'INFO',
            'ip': user_pkg.user_object.socket.get_extra_info('peername'),
            'message': 'Authentication process initialized',
        }
    )

    return ('displayed_login_title', user_pkg)

async def _state_login_prompt(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the initial login prompt text block.

    Transition(s):
        'prompted_for_login' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000001').encode('ascii'))
    await user_pkg.user_object.socket.drain()

    return ('prompted_for_login', user_pkg)

async def _state_login_process(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which processes returned user input from login prompt.

    Transition(s):
        'login_processed' if user provides account name
        'create_initial_state' if user chooses to create account
        'error_state' on connection failure

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_input = await user_pkg.input_reader.read(100)

    # connection is broken, go to error_state
    if user_input == b'':
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Connection lost during _state_login_process',
            }
        )
        return ('error_state', user_pkg)

    user_input = user_input.decode().rstrip()

    # user chose to create new account, create AccountCreation object
    if user_input == 'c':
        user_pkg.input_tracker = AccountCreation()

        await logger_manager.authorization.info(
            {
                'type': 'INFO',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Account creation initiated',
            }
        )

        return ('create_initial_state', user_pkg)

    # user chose to input account name, create SimpleAuth object and assign account_name
    # if input_track is already SimpleAuth we are on a multiple login attempt
    if user_pkg.input_tracker != SimpleAuth():
        user_pkg.input_tracker = SimpleAuth()

    user_pkg.input_tracker.account_name = user_input
    user_pkg.user_login_attempts += 1

    await logger_manager.authorization.info(
        {
            'type': 'INFO',
            'ip': user_pkg.user_object.socket.get_extra_info('peername'),
            'message': f'Account login initiated for user: {user_pkg.input_tracker.account_name}... attempt {user_pkg.user_login_attempts}'
        }
    )

    return ('login_processed', user_pkg)

async def _state_password_prompt(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the password prompt text block.

    Transition(s):
        'prompted_for_password' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000002').encode('ascii'))
    await user_pkg.user_object.socket.drain()

    return ('prompted_for_password', user_pkg)

async def _state_password_process(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which processes returned user input from password prompt.

    Transition(s):
        'password_processed' on success
        'error_state' on connection failure

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_input = await user_pkg.input_reader.read(100)

    # connection is broken, go to error_state
    if user_input == b'':
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Connection lost during _state_password_process'
            }
        )

        return ('error_state', user_pkg)

    user_pkg.input_tracker.password = user_input.decode().rstrip()

    return ('password_processed', user_pkg)

async def _state_validate(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which validates user and password information submitted by user.

    Transition(s):
        'error_state' if user is already logged in or user reach maximum login tries
        'displayed_login_title' if account name does not exist or password is incorrect
        'validated' if validation of account name and password is successful

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    # TODO STRETCH: show bad login attempts to user upon successful login
    query_account_name = 'SELECT account_name FROM users WHERE account_name=?'
    query_account_password = 'SELECT password FROM users WHERE account_name=?'
    valid_account_name = False
    valid_password = False

    # validate that user is not already logged in
    if manager_hub.user_manager.is_logged_in(user_pkg.input_tracker.account_name):
        user_pkg.user_object.socket.write(get_block('000008').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': f'Validation error - user already logged in for user: {user_pkg.input_tracker.account_name}'
            }
        )

        return ('error_state', user_pkg)

    # validate user exists in database
    if await query_table(query_account_name, (user_pkg.input_tracker.account_name,)):
        valid_account_name = True

        # validate user password matches password for account in database
        query_results = await query_table(query_account_password, (user_pkg.input_tracker.account_name,))

        if bcrypt.checkpw(user_pkg.input_tracker.password.encode(), query_results[0][0]):
            valid_password = True
        else:
            await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': f'Validation error - password does not match for entered user: {user_pkg.input_tracker.account_name}'
            }
        )
    else:
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': f'Validation error - user does not exist in database for entered user: {user_pkg.input_tracker.account_name}'
            }
        )

    if not valid_account_name or not valid_password:
        # return to the login prompt as user has not reached maximum retries
        if user_pkg.user_login_attempts <= 4:
            user_pkg.user_object.socket.write(get_block('000009').encode('ascii'))
            await user_pkg.user_object.socket.drain()

            return ('displayed_login_title', user_pkg)

        # user has reached maximum retries.  Transition to error state and disconnect their session
        user_pkg.user_object.socket.write(get_block('000010').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': f'Validation error - maximum retries reached for user: {user_pkg.input_tracker.account_name}'
            }
        )

        return ('error_state', user_pkg)

    return ('validated', user_pkg)

async def _state_authorized(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sets the authorized value to True.

    Transition(s):
        'authorized' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.set_authorized(True)
    user_pkg.user_object.account_name = user_pkg.input_tracker.account_name

    await logger_manager.authorization.info(
        {
            'type': 'INFO',
            'ip': user_pkg.user_object.socket.get_extra_info('peername'),
            'message': f'Account login authorized for user: {user_pkg.input_tracker.account_name}'
        }
    )

    return ('authorized', user_pkg)

async def _state_new_account_prompt(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the new account name prompt text block.

    Transition(s):
        'prompted_for_new_account_name' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000003').encode('ascii'))
    await user_pkg.user_object.socket.drain()

    return ('prompted_for_new_account_name', user_pkg)

async def _state_new_account_process(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which processes returned user input from new account name prompt.

    Transition(s):
        'new_account_name_processed' on success
        'create_initial_state' if account name already exists in database
        'create_initial_state' if account name doesn't meet length requirements
        'create_initial_state' if account name start with non-[a-Z] character or containes whitespace
        'create_initial_state' if account name contains ANSI sequence
        'error_state' on connection failure

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_input = await user_pkg.input_reader.read(100)
    query_account_name = 'SELECT account_name FROM users WHERE account_name=?'

    if user_input == b'':
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Connection lost during _state_new_account_process'
            }
        )

        return ('error_state', user_pkg)

    user_input = user_input.decode().rstrip()

    # force another account_name prompt if user_input already exists as an account name
    if await query_table(query_account_name, (user_input,)):
        user_pkg.user_object.socket.write(get_block('000017').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('create_initial_state', user_pkg)

    # force another account_name prompt if user_input doesn't meet length requirements
    if len(user_input) < 4 or len(user_input) > 20:
        user_pkg.user_object.socket.write(get_block('000011').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('create_initial_state', user_pkg)

    # force another account_name prompt if user_input starts with non-char or contains space
    if re.search(r'^[0-9]|\s', user_input):
        user_pkg.user_object.socket.write(get_block('000012').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('create_initial_state', user_pkg)

    # force another account_name prompt if user_input includes ANSI escape sequences
    if re.search(r'\\033\[.*m', user_input):
        user_pkg.user_object.socket.write(get_block('000013').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('create_initial_state', user_pkg)

    user_pkg.input_tracker.account_name = user_input

    return ('new_account_name_processed', user_pkg)

async def _state_real_name_prompt(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the real name prompt text block.

    Transition(s):
        'prompted_for_real_name' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000004').encode('ascii'))

    return ('prompted_for_real_name', user_pkg)

async def _state_real_name_process(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which processes returned user input from real name prompt.

    Transition(s):
        'real_name_processed' on success
        'error_state' on connection failure

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_input = await user_pkg.input_reader.read(100)

    if user_input == b'':
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Connection lost during _state_real_name_process'
            }
        )

        return ('error_state', user_pkg)

    user_input = user_input.decode().rstrip()

    user_pkg.input_tracker.real_name = user_input

    return ('real_name_processed', user_pkg)

async def _state_new_password_prompt(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the new password prompt text block.

    Transition(s):
        'prompted_for_new_password' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000005').encode('ascii'))

    return ('prompted_for_new_password', user_pkg)

async def _state_new_password_process(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which processes returned user input from new password prompt.

    Transition(s):
        'new_password_processed' on success
        'real_name_processed' if password doesn't meet length requirements
        'real_name_processed' if password contains a space
        'error_state' on connection failure

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_input = await user_pkg.input_reader.read(100)

    if user_input == b'':
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Connection lost during _state_new_password_process'
            }
        )

        return 'error_state'

    user_input = user_input.decode().rstrip()

    # force another password prompt if user_input doesn't meet length requirements
    if len(user_input) < 10 or len(user_input) > 30:
        user_pkg.user_object.socket.write(get_block('000014').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('real_name_processed', user_pkg)

    # force another password prompt if user_input includes a space
    if re.search(r'\s', user_input):
        user_pkg.user_object.socket.write(get_block('000015').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('real_name_processed', user_pkg)

    user_pkg.input_tracker.password = user_input

    return ('new_password_processed', user_pkg)

async def _state_reenter_new_password_prompt(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the re-enter new password prompt text block.

    Transition(s):
        'prompted_for_reenter_new_password' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000006').encode('ascii'))

    return ('prompted_for_reenter_new_password', user_pkg)

async def _state_reenter_new_password_process(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which processes returned user input from re-enter new password prompt.

    Transition(s):
        'reenter_new_password_processed' on success
        'real_name_processed' if password password comparison fails
        'error_state' on connection failure

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_input = await user_pkg.input_reader.read(100)

    if user_input == b'':
        await logger_manager.authorization.warning(
            {
                'type': 'WARNING',
                'ip': user_pkg.user_object.socket.get_extra_info('peername'),
                'message': 'Connection lost during _state_reenter_new_password_process'
            }
        )

        return ('error_state', user_pkg)

    user_input = user_input.decode().rstrip()

    # if password comparison fails, transition user to state to enter account password
    if user_pkg.input_tracker.password != user_input:
        user_pkg.user_object.socket.write(get_block('000016').encode('ascii'))
        await user_pkg.user_object.socket.drain()

        return ('real_name_processed', user_pkg)

    return ('reenter_new_password_processed', user_pkg)

async def _state_create_new_account(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which creates new user account in database.

    Transition(s):
        'new_account_created' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    # generate salt and hash password prior to writing to DB
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user_pkg.input_tracker.password.encode(), salt)
    hashed_real_name = bcrypt.hashpw(user_pkg.input_tracker.real_name.encode(), salt)

    # insert new account information into 'user' table
    await insert_user_account(
        user_pkg.input_tracker.account_name,
        hashed_real_name,
        hashed_password,
    )

    await logger_manager.authorization.info(
        {
            'type': 'INFO',
            'ip': user_pkg.user_object.socket.get_extra_info('peername'),
            'message': 'Account creation successful'
        }
    )

    return ('new_account_created', user_pkg)

async def _state_inform_of_login(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State which sends the account created prompt text block.

    Transition(s):
        'auth_initial_state' on success

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.socket.write(get_block('000007').encode('ascii'))
    await user_pkg.user_object.socket.drain()

    return ('auth_initial_state', user_pkg)

async def _state_error(user_pkg: UserAuthPackage) -> tuple[str, UserAuthPackage]:
    """State is an endpoint for all non-recoverable errors.  Sets user authorized to False.

    Transition(s):
        None

    Parameters
    ----------
    user_pkg : UserAuthPackage
        Instance of UserAuthPackage which stores authorization information during authorization process

    Returns
    -------
    tuple[str, UserAuthPackage]
        [Transition State, Instance of UserAuthPackage]
    """
    user_pkg.user_object.set_authorized(False)

    return (None, user_pkg)
