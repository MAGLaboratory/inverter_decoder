##
## This file was part of the libsigrokdecode project.
##
## Copyright (C) 2026 Brandon Kirisaki <b.k.lu@ieee.org>
## Copyright (C) 2016 Vladimir Ermakov <vooon341@gmail.com>
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

import sigrokdecode as srd
from functools import reduce
from .debounce import Debounce

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'inverter_control_panel'
    name = 'Inverter Control Panel Decoder'
    longname = 'Inverter single-wire communication protocol decoder'
    desc = 'Inverter control panel decoder'
    license = 'gplv3+'
    inputs = ['logic']
    outputs = []
    tags = ['Display', 'Panel', 'Power']
    channels = (
        {'id': 'din', 'name': 'DIN', 'desc': 'DIN data line'},
    )
    options = (
        {'id': 'debounce', 'desc': 'Number of samples to debounce',
            'default': 3, 'values': tuple(range(100))},
    )
    annotations = (
        ('bit', 'Bit'),
        ('reset', 'RESET'),
        ('byte', 'Byte'),
        ('dup', 'Duplicate'),
        ('iv', 'Input Voltage'),
        ('ov', 'Output Voltage'),
        ('w', 'Wattage'),
    )
    annotation_rows = (
        ('bit', 'Bits', (0, 1)),
        ('byte', 'Byte', (2,)),
        ('dup', 'Duplication', (3,)),
        ('dec', 'Decode', (4,5,6)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.olddpin = None
        self.ss_packet = None
        self.sss_packet = None
        self.ss = None
        self.es = None
        self.bits = []
        self.bytes = []
        self.nibbles = []
        self.nl = []
        self.nibble = []
        self.inreset = False

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.debounce = Debounce(None, self.options['debounce'])

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def handle_bits(self, samplenum):
        if len(self.bits) == 8:
            self.bits = reversed(self.bits)
            byte = reduce(lambda a, b: (a << 1) | b, self.bits)
            self.put(self.ss_packet, samplenum, self.out_ann,
                     [2, ['0x%02X' % byte]])
            self.bytes.append(byte)
            self.nl.append(self.ss_packet)
            self.bits = []
            self.ss_packet = None

    def handle_bytes(self, samplenum):
        if len(self.bytes) == 2:
            if self.bytes[0] == self.bytes[1]:
                self.put(self.sss_packet, samplenum, self.out_ann, 
                     [3, [f"OK 0x{self.bytes[0]:02X}"]])
                self.nibbles.append(self.bytes[0] >> 4)
                self.nibbles.append(self.bytes[0] & 0xF)
            else:
                self.put(self.sss_packet, samplenum, self.out_ann, 
                     [3, [f"NO 0x{self.bytes[0]:02X}"]])

            self.bytes = []
            self.sss_packet = None

    def handle_decode(self):
        if len(self.nibbles) == 12 and len(self.nl) == 13:
            iv = reduce(lambda a, b: (a << 4) | b, self.nibbles[2:5])
            iv /= 48
            self.put(self.nl[2], self.nl[5], self.out_ann,
                [4, [f"{iv:.2f}"]])
            ov = reduce(lambda a, b: (a << 4) | b, self.nibbles[6:8])
            self.put(self.nl[6], self.nl[8], self.out_ann,
                [5, [f"{ov}"]])
            w = reduce(lambda a, b: (a << 4) | b, self.nibbles[8:12])
            w //= 7
            self.put(self.nl[8], self.nl[12], self.out_ann,
                [6, [f"{w}"]])
            
        

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        while True:
            # TODO: Come up with more appropriate self.wait() conditions.
            # pin is the value of the pin
            (pin,) = self.wait()

            dpin = self.debounce.update(pin)

            if self.olddpin is None:
                self.olddpin = dpin
                continue

            # Check RESET condition
            if not self.inreset and pin and self.es is not None and \
                    self.ss is not None and \
                    (self.samplenum - self.es) / self.samplerate > 10e-3:

                # Decode last bit value.
                tL = (self.es - self.ss) / self.samplerate
                bit_ = False if tL >= 205e-6 else True

                self.bits.append(bit_)
                self.handle_bits(self.es)
                self.handle_bytes(self.es)

                self.put(self.ss, self.es, self.out_ann, [0, ['%d' % bit_]])
                self.put(self.es, self.samplenum, self.out_ann,
                         [1, ['RESET', 'RST', 'R']])

                self.nl.append(self.es)
                self.handle_decode()

                self.inreset = True
                self.bits = []
                self.ss_packet = None
                self.bytes = []
                self.nibbles = []
                self.nl = []
                self.sss_packet = None
                self.ss = None
                self.nibble = []

            if  self.olddpin and not dpin:
                # falling edge.
                if self.ss and self.es:
                    period = self.samplenum - self.ss
                    duty = self.es - self.ss
                    # Ideal duty for T0H: 33%, T1H: 66%.
                    bit_ = (duty / period) < 0.5

                    self.put(self.ss, self.samplenum, self.out_ann,
                             [0, ['%d' % bit_]])

                    self.bits.append(bit_)
                    self.handle_bits(self.samplenum)
                    self.handle_bytes(self.samplenum)

                if self.ss_packet is None:
                    self.ss_packet = self.samplenum

                if self.sss_packet is None:
                    self.sss_packet = self.samplenum

                self.ss = self.samplenum

            elif not self.olddpin and dpin:
                # rising edge.
                self.inreset = False
                self.es = self.samplenum

            self.olddpin = dpin
