Inverter Control Panel Decoder
========================

Simple and naive decoder, but it works.

![Image of the protocol decoder featuring the various fields that are supposed to be decoded](/img/screenshot.png)

Notes
-----
This decoder is currently a work in progress.

Tests are not run on the code and no linter is used to check for code quality.

User discretion is advised.

Concept of Execution
--------------------
The bit data from communications is often noisy.  The bus idle state is high.
Measured bit timing is 410 us.  `0` bits are 320 us of logic low followed by
90 us of logic high.  `1` bits are 120 us of logic high followed by 290 us of
logic high.

The bit data is first run through `debouncer.py`.

The debounced data is run through falling edge detection.

Between the two falling edges, the 50% point is detected and sampled.  If the
sample is logic low, the bit is  `0`.  If the sample is logic high, the bit is
`1`.

Protocol Description
--------------------
The protocol is implemented in a relatively straightforward manner...
Each byte is sent LSB first and repeated twice.

Data in the sent packet is always 6 bytes long and can be grouped into 
nibbles.

<table>
    <tr>
        <td>0</td>
        <td>1</td>
        <td>2</td>
        <td>3</td>
        <td>4</td>
        <td>5</td>
        <td>6</td>
        <td>7</td>
        <td>8</td>
        <td>9</td>
        <td>10</td>
        <td>11</td>
    </tr>
    <tr>
        <td>Unk</td>
        <td>System Nibble<br>`0x2`: Normal<br>`0x4`: Button Down<br>`0x1`: Shutting Down<br>`0x8`: Shutdown</td>
        <td colspan=3>Input voltage x48</td>
        <td>Utility Nibble<br>`0xB`: Fan Off<br>`0xF`: Fan On<br>`0x5`: Inv Off</td>
        <td colspan=2>Output Voltage</td>
        <td colspan=4>Wattage x7</td>
    </tr>
</table>

Installation
------------

```
mkdir -p ~/.local/share/libsigrokdecode/decoders
cd ~/.local/share/libsigrokdecode/decoders
git clone https://github.com/MAGLaboratory/inverter_decoder/
```

Thanks
------
Thanks are owed to the original author of the `ws281x` decoder for libsigrokdecoders: Vladimir Ermakov https://github.com/vooon 

This repository was originally forked from their repository and deviated enough from the original that it made sense to separate it from the fork network.  The original code is available at the following repository: https://github.com/vooon/sigrok-rgb_led_ws281x 
