Shannon LTE CA editor
=====================

A Python/Tkinter-based GUI editor to edit LTE CA combos on Google Pixel 9 and 10 with a bunch of useful tools to save editing effort.

Features
--------

- Import/export LTE .binarypb files directly
- Import/export as protobuf .txt formats
- View LTE combinations in a searchable table w/plmn filtering
- Edit LTE bands, assign DL/UL bw classes, MIMO, BCS, and plmn mappings
- Add, duplicate, delete, and reorder any combos
- Add, delete, and reorder CCs in each combo
- Auto-generate CA combos and auto UL assignment to save time!
- Prune combos to reduce message size with band filter and/or intra-band CA exclusion
- Apply conf_id bitmasks (plmn mapping) to all combinations or selected bands
- Validate and automatically repair any typos or unsupported configurations, such as low-band 4x4 or illegal B7, B38 uplink assignment, etc.

Validation Checks
-----------------

After editing the combos, you can use the "validation" feature to check for any errors/typos/bad configurations such as:

- Duplicates
- Missing uplink
- B7/B38 uplink assignments if a combo contains 7+38
- Accidental uplink assignments on SDL bands
- Exceed 24 spatial streams
- Unsupported low-band combinations (only 20+28 is supported)
- Invalid DL/UL bw classes
- Unsupported 4x4 DL MIMO assignments on low bands

Some of the errors can be fixed automatically, while some can only be highlighted for manual review.

Requirements
------------

- Python 3.10 or newer
- protobuf
- PyInstaller, only when building a standalone executable

Install dependencies with:

    py -m pip install protobuf pyinstaller

Running
-------
For Windows users, you can download the executable from the **Releases** section and run it directly without installing any dependencies. Alternatively, you can run `main.py`.

From the project folder:

    py main.py

Using the auto combo generator
--------------------------
<img width="642" height="331" alt="image" src="https://github.com/user-attachments/assets/0d47df04-569f-405a-97a7-8d389ef6af46" />


Step 1: Input a "large" combo such as
```1+1+3+3+8B+28+32+40D+41```.
The function will generate the subsets such as ```1+1```, ```1+3```, ```1+3+8```, ```1+3+8B```, ```1+1+3+28```, ```1+40```. ```1+40C```etc, and assign the appropriate bw classes and mimo capability to each of them automatically.

The generator automatically avoids "impossible" configurations such as:

- Anything besides ```20+28``` for low band CA
- 4x4 MIMO on low bands or B21
- Uplink on SDL
- Uplink on B7 or B38 if the combo contains ```7+38```

If a combo contains more than 24 spatial streams, the algorithm will generate subvariants with nerfed MIMO automatically. 
For example, ```1C+3C+7C+28``` with MIMO ```4+4+4+4+4+4+2 (26)``` will be broken into the following MIMO subsets:
- ```2+2+4+4+4+4+2```
- ```4+4+2+2+4+4+2```
- ```4+4+4+4+2+2+2```

If your network has a max-cc limit,

Using the auto combo generator
--------------------------


Bandwidth classes and MIMO per CC component
-----------------

Class A = 1 CC
Class B = 2 CC
Class C = 2 CC
Class D = 3 CC
Class E = 4 CC
Class F = 5 CC

The least-significant bit of the DL value represents MIMO mode:

Even value
    2x2 DL MIMO

Odd value
    4x4 DL MIMO

Examples:

    32768 = Class A, 2x2
    32769 = Class A, 4x4
    8192  = Class C, 2x2
    8193  = Class C, 4x4

Combo Pruning
-------------

Example allowed-band list:

    1, 3, 8, 28, 40, 41

Example exclusions:

    1+1, 3+3, 40D, 41E

Meaning:

    1+1
        Remove combinations containing repeated Band 1 components.

    40D
        Remove Band 40 Class D and higher.
        Lower classes such as 40A and 40C remain allowed.

conf_id Handling
----------------

The program stores conf_id mappings using two bitmasks:

configMaskLow
    conf_id 0 through 63

configMaskHigh
    conf_id 64 through 95

The GUI can convert between named conf_id entries and the two mask values.

Building a Windows Executable
-----------------------------

From the project folder:

    py -m PyInstaller --noconfirm --onefile --windowed ^
      --name "Shannon LTE CA editor" ^
      --collect-all google.protobuf ^
      main.py

Single-line version:

    py -m PyInstaller --noconfirm --onefile --windowed --name "Shannon LTE CA editor" --collect-all google.protobuf main.py

The executable will be created in the dist folder.

Project Files
-------------

main.py
    Main Tkinter application.

utils.py
    Protobuf parsing, import/export, data models, UL generation,
    validation, repair, and shared LTE utilities.

custom_utils.py
    Custom-combination generation, band filtering, exclusion rules,
    DL MIMO generation, and hardware-limit handling.

tools_ui.py
    Dialog windows for generation, pruning, conf_id mapping,
    validation, and repair.

conf_id.py
    conf_id names (plmn groups) and bitmask conversion helpers.

Important Notes
---------------

- Keep main.py, utils.py, custom_utils.py, tools_ui.py, and conf_id.py in the same folder.
- Always keep a backup of the original .binarypb file.
- Validation cannot guarantee modem or network compatibility.
- Some combinations may be syntactically valid but unsupported by a specific device, firmware, carrier configuration, or radio front end.
- Test modified capability files carefully.

Credits / Acknowledgements
----------
Protobuf definition obtained from [uecapabilityparser](https://github.com/HandyMenny/uecapabilityparser)
