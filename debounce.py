##
##
## Copyright (C) 2026 Brandon Kirisaki <b.k.lu@ieee.org>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

class Debounce:
    # holdoff is the state where the input is different from the debounced value
    holdoff = False
    def __init__(self, initial, delay):
        self.delay = delay
        self.debounced = initial

    # returns the debounced value
    def update(self, newValue):
        # when holdoff is true, the last value did not match the debounced value
        if self.holdoff:
            if newValue == self.debounced:
                self.holdoff = False;
            elif self.time >= self.delay:
                self.debounced = newValue
                self.holdoff = False
                return self.debounced
            else:
                self.time += 1
                return self.debounced
        else:
            if newValue != self.debounced:
                # two because it is confirmed this sample
                # and we are not using zero-indexed sample counters
                self.time = 2
                self.holdoff = True
                return self.debounced
            else:
                return self.debounced
