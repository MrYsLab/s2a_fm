s2a_fm
======

Arduino users! Would you like to configure and control your Arduino micro-controller without having
to write a single line of Arduino sketch code and at the same time have access to a graphical user
interface?

Scratch and Snap! programmers! Would you like to control and communicate with an Arduino board using
Scratch? Imagine, using Scratch to control physical devices such as LEDs, motors, and relays while
monitoring devices, such as temperature sensors, potentiometers, and light sensors. What would you
create?

s2a_fm is a Scratch/Snap! hardware extension written in Python allowing Scratch or Snap! and an Arduino
micro-controller to communicate seamlessly.

Program Block translations are included for Chinese, Dutch, English (default) French, and Spanish.

Make sure you get the latest version of the Scratch Off-Line editor if you are using Scratch.

At this point in time, Snap! has a more stable hardware interface than Scratch, so it is recommended for use.


Installation Instructions
--------------------------
The s2a_fm Reference Manual, s2a_fm_reference.pdf, located in the documentation directory of this distribution,
provides full installation instructions

Version 1.4 Mar 23, 2014
-----------------------
New Feature for 1.4

Chinese translation of Block Text provided through the generosity of Professor YuFangjun

French translation of Block Text provided through the generosity of Professor Sebastien Canet
.

Version 1.3 Feb 23, 2014
------------------------
New Features for 1.3

1. Support for the upcoming Snap!Mobile Physical Computing Project in "Instructables"

2. Spanish Translation of Block Text and a Spanish Tutorial provided courtesy of Professor
José Manuel Ruiz


Version 1.2 Jan 1, 2014
-----------------------
New Features for 1.2:

1. Support for Snap! 4.0 provided.

2. Support for up to 4 simultaneous HC-SR04 type "Ping" Sensors.
(This requires using PyMata version 1.54 or greater and the FirmataPlus Arduino sketch supplied with PyMata 1.54).

3. Dutch translation for the Scratch/Snap! Block Text included (Thanks to Sjoerd Dirk Meijer).

4. Provision to translate Scratch/Snap! Block Text to any language.

Version 1.1 December 19, 2013
-----------------------------

New Features for 1.1:

1. When enabling a digital pin, the pin capabilty is verified for the requested mode.

2. A new Scratch debugger command block has been added to help debug Scratch scripts.

Known Snap! 4.0 Extension Issues
----------------------
None.


Known Scratch 2.0 Extension Issues
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

Snap! s2a_fm Extension Blocks
-----------------------------
![ScreenShot](https://raw.github.com/MrYsLab/s2a_fm/master/documentation/snap_blocks.png)

Wiring Diagrams for Examples
----------------------------

![ScreenShot](https://raw.github.com/MrYsLab/s2a_fm/master/documentation/LED_EXAMPLE.png)

![ScreenShot](https://raw.github.com/MrYsLab/s2a_fm/master/documentation/pot1.png)

