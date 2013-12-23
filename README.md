s2a_fm
======

Arduino users! Would you like to configure and control your Arduino micro-controller without having
to write a single line of Arduino sketch code and at the same time have access to a graphical user
interface?

Scratch programmers! Would you like to control and communicate with an Arduino board using
Scratch? Imagine, using Scratch to control physical devices such as LEDs, motors, and relays while
monitoring devices, such as temperature sensors, potentiometers, and light sensors. What would you
create?

s2a_fm is a Scratch hardware extension written in Python allowing Scratch and an Arduino
micro-controller to communicate seamlessly.

Make sure you get the latest version of the Scratch Off-Line editor.

Version 1.2 December 23, 2013
-----------------------------

New Feature for 1.2 (contributed by Sjoerd Dirk Meijer, fromScratchEd.nl):

- Language support
	1. copy s2a_fm.s2e to a new file, i.e. s2a_fm_NL.s2e

		translate every second line inside a block

			don't change the sequence of the variables on these lines!!

		translate the variables, except PIN, VAL and words with underscores ('_')

	2. scratch_command_handlers.py: add your translations to the variables starting with 'ln_', i.e.

		ln_ENABLE = ['Enable', 'aan', '{your translation}']	

Version 1.1 December 19, 2013
-----------------------------

New Features for 1.1:

1. When enabling a digital pin, the pin capabilty is verified for the requested mode.

2. A new Scratch debugger command block has been added to help debug Scratch scripts.


Known Scratch 2.0 Issues
------------

A.  The current version of Scratch 2.0 does not properly restart a Scratch program when clicking the red stop button
and pressing the green start flag again.

             Workarounds: 1. Close Scratch and reopen it.
                          2. Click the When (Green Flag) Clicked block in the editor.

B. Placing a Scratch Extension Command Block in a loop construct causes the loop to execute once and then abort.

             Workaround: Either write scripts in a linear fashion or use broadcast messages to
             execute the extension command block.

Scratch s2a_fm Extension Blocks
-------------------------------

![ScreenShot](https://raw.github.com/MrYsLab/s2a_fm/master/documentation/scratch_blocks.png)


Wiring Diagrams for Examples
----------------------------

![ScreenShot](https://raw.github.com/MrYsLab/s2a_fm/master/documentation/LED_EXAMPLE.png)

![ScreenShot](https://raw.github.com/MrYsLab/s2a_fm/master/documentation/pot1.png)

