# sfrtvctl

python library which can also be use in command line.

Summary
==========

commands are sent by websocket on port 7682 with sub-protocol lws-bidirectional-protocol.

there is multiple kind of data structure depending on kind of commands we went to send.

send commands :
BUTTONEVENT structure for  classical remote keys (volume, power, ok, return, pause, play, forward, rewind, directionnal keys, num pad)
ZAP structure to send a channel number in 1 request.
APP structure to launch special function of the decoder (mosaic, tv guide, vod, replay, recording, media center, settings)
SETVOLUME structure to set the volume
KEYBOARD structure to type when inside input field

Info commands (not yet implemented):
GETINFO and GETVERSION

Installation
============

samsungctl can be installed using `pip <(https://pip.pypa.io/>`_:

::

    # pip install websocket-client
    # pip install sfrtvctl

Alternatively you can clone the Git repository and run:

::

    # python setup.py install

It's possible to use the command line tool without installation:

::

    $ python -m sfrtvctl

BUTTONEVENT
============

BUTTONEVENT take a second argument to specify the key pressed and a third in case you specify NUM.

the table here resume each possible actions for BUTTONEVENT :

| Key Pressed (second argument)  | Description                                      |
| ------------------------------ | -------------------------                        |
| VUP                            | Volume up                                        |
| VDOWN                          | Volume Down                                      |
| RIGHT                          | multidirectionnal right                          |
| LEFT                           | multidirectionnal left                           |
| UP                             | multidirectionnal up                             |
| DOWN                           | multidirectionnal down                           |
| PUP                            | Program up                                       |
| PDOWN                          | Program down                                     |
| INFO                           | Current program info                             |
| RETURN                         | return key                                       |
| OK                             | OK key                                           |
| NUMBER                         | a digit key. take a third argument for the digit |
| PLAYPAUSE                      | play or pause key                                |
| FORWARD                        | fast forward key                                 |
| REWIND                         | fast rewind  key                                 |
| MUTE                           | mute sound key                                   |
| POWER                          | power on/off key                                 |

in command line mode here is an example of command :
```sfrtvctl --host BUTTONEVENT VUP``` # increase volume
```sfrtvctl --host BUTTONEVENT NUMBER 1``` # type 1 on num pad (will change channel if watching tv)

ZAP
====

ZAP command is simple, it just take a number as second argument.

in command line mode here is an example of command :
```sfrtvctl --host ZAP 180``` # will go to channel 180

APP
===

| Command       | Description                       |
| ------------- | --------------------------------- |
| MOSAIC        | Mosaique                          |
| TVGUIDE       | Guide TV                          |
| VOD           | SFR Play                          |
| REPLAY        | TV replay                         |
| RECORDING     | List recorded shows               |
| MEDIACENTER   | media center (usb, network media) |
| SETTINGS      | Decoder settings                  |

in command line mode here is an example of command :
```sfrtvctl --host MOSAIC``` # will display mosaique

SETVOLUME
==========

SETVOLUME command is simple, it just take a number between 1 and 100 as second argument to set volume.

in command line mode here is an example of command :
```sfrtvctl --host SETVOLUME 40``` # will set volume to 40

KEYBOARD
=========

will send keyboard data. This command has a special character to start search which you can send by passing SEARCH as a second argument. To start typing you must send first VALUE and then a third argument.

| Command       | Description                              |
| ------------- | ---------------------------------------- |
| SEARCH        | Start search                             |
| VALUE         | send keyboard key pass in third argument |


in command line mode here is an example of command :
```sfrtvctl --host SEARCH``` # will start search
```sfrtvctl --host VALUE a``` # will type a in an input field


Library usage
=============

sfrtvctl can be imported as a Python 3 library:

.. code-block:: python

    import sfrtvctl

A context managed remote controller object of class ``Remote`` can be
constructed using the ``with`` statement:

.. code-block:: python

    with sfrtvctl.Remote(config) as remote:
        # Use the remote object

The constructor takes a configuration dictionary as a parameter. All
configuration items must be specified.

| Key     | Type   | Description                                 |
|---------|--------|---------------------------------------------|
| host    | string | Hostname or IP address of the decoder.      |
| port    | int    | TCP port number. (Default: ``7682``)        |
| timeout | int    | Timeout in seconds. ``0`` means no timeout. |

The ``Remote`` object is very simple and you only need the ``control(key, arg1, arg2)``
method. See tables above for more details about commands you can pass. You can call ``control`` multiple times
using the same ``Remote`` object. The connection is automatically closed when
exiting the ``with`` statement.
