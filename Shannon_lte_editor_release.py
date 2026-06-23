import re
import sys
from itertools import combinations
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

try:
    from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
except ImportError:
    descriptor_pb2 = None
    descriptor_pool = None
    message_factory = None

### Proto ###
    
def build_shannon_lte_message_class():
    if descriptor_pb2 is None:
        raise RuntimeError(
            "Binary protobuf support requires the protobuf package.\n\n"
            "Install w/ pip install protobuf"
        )

    fd = descriptor_pb2.FileDescriptorProto()
    fd.name = "shannon_lte_ue_cap.proto"
    fd.syntax = "proto2"

    component = fd.message_type.add()
    component.name = "Component"
    for name, number in (("band", 1), ("bwClassMimoDl", 2), ("bwClassMimoUl", 3)):
        f = component.field.add()
        f.name = name
        f.number = number
        f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REQUIRED
        f.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32

    combo = fd.message_type.add()
    combo.name = "Combo"
    f = combo.field.add()
    f.name = "components"
    f.number = 1
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    f.type_name = ".Component"
    f = combo.field.add()
    f.name = "bcs"
    f.number = 2
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_UINT32

    # conf_id 0..63
    f = combo.field.add()
    f.name = "configMaskLow"
    f.number = 3
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REQUIRED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_UINT64

    # conf_id 64..95
    f = combo.field.add()
    f.name = "configMaskHigh"
    f.number = 4
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REQUIRED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_UINT32

    root = fd.message_type.add()
    root.name = "ShannonLteUECap"
    f = root.field.add()
    f.name = "version"
    f.number = 1
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REQUIRED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_UINT32
    f = root.field.add()
    f.name = "combos"
    f.number = 2
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    f.type_name = ".Combo"
    f = root.field.add()
    f.name = "bitmask"
    f.number = 3
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REQUIRED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_UINT32

    pool = descriptor_pool.DescriptorPool()
    pool.Add(fd)
    desc = pool.FindMessageTypeByName("ShannonLteUECap")
    if hasattr(message_factory, "GetMessageClass"):
        return message_factory.GetMessageClass(desc)
    return message_factory.MessageFactory(pool).GetPrototype(desc)

###########


DL_VALUE_OPTIONS = [
    ("32768", "32768 (A)"),
    ("32769", "32769 (A 4×4)"),
    ("16384", "16384 (B)"),
    ("16385", "16385 (B 4×4)"),
    ("8192", "8192 (C)"),
    ("8193", "8193 (C 4×4)"),
    ("4096", "4096 (D)"),
    ("4097", "4097 (D 4×4)"),
    ("2048", "2048 (E)"),
    ("2049", "2049 (E 4×4)"),
    ("1024", "1024 (F)"),
    ("1025", "1025 (F 4×4)"),
]

UL_VALUE_OPTIONS = [
    ("0", "0 (Disabled)"),
    ("32768", "32768 (A)"),
    ("8192", "8192 (C)"),
    ("4096", "4096 (D)"),
]

# BCS
BCS_VALUE_OPTIONS = [
    ("2147483648", "2147483648 (BCS 0)"),
    ("3221225472", "3221225472 (BCS 0, 1)"),
    ("3758096384", "3758096384 (BCS 0, 1, 2)"),
    ("4026531840", "4026531840 (BCS 0, 1, 2, 3)"),
    ("4160749568", "4160749568 (BCS 0, 1, 2, 3, 4)"),
    ("4227858432", "4227858432 (BCS 0, 1, 2, 3, 4, 5)"),
    
]
BCS_VALUE_TO_LABEL = dict(BCS_VALUE_OPTIONS)
BCS_LABEL_TO_VALUE = {label: value for value, label in BCS_VALUE_OPTIONS}

CONF_ID_NAMES = {
    0: "Default",
    1: "VZW",
    2: "TMO",
    3: "ATT",
    4: "SPRINT",
    5: "USC",
    6: "DISH",
    7: "ROGERS",
    8: "TELUS",
    9: "BELL",
    10: "FREEDOM",
    11: "VIDEOTRON",
    12: "RAKUTEN",
    13: "DCM",
    14: "SBM",
    15: "KDDI",
    16: "DT_DE",
    17: "VF_DE",
    18: "O2_DE",
    19: "VF_UK",
    20: "EE",
    21: "O2_UK",
    22: "3_UK",
    23: "VF_IE",
    24: "ORANGE_FR",
    25: "BOUYGUES",
    26: "SFR",
    27: "FREE_FR",
    28: "MOVISTAR_ES",
    29: "VF_ES",
    30: "ORANGE_ES",
    33: "DT_PL",
    34: "VF_IT",
    35: "TIM_IT",
    36: "WINDTRE",
    37: "VF_TR",
    38: "VF_RO",
    39: "TELSTRA",
    40: "OPTUS",
    41: "VHA",
    42: "TWM",
    43: "FET",
    44: "CHT",
    45: "SINGTEL",
    46: "STARHUB",
    47: "M1",
    50: "TEST_LAB",
    51: "CSPIRE",
    52: "CELLCOM",
    53: "T_STAR",
    54: "RJIO",
    55: "VF_CZ",
    56: "3_IE",
    57: "VODA_IDEA",
    58: "VF_IN",
    59: "AIRTEL",
    60: "EU_COMMON",
    61: "GOOGLE_COMCAST_",
    62: "EU_GENERIC_3CA",
    63: "APAC_COMMON",
    64: "EU_COMMON1",
    65: "1_1_DE",
    66: "TEST_FIELD_NA",
    67: "TEST_FIELD_ROW",
    68: "TELIA_NO",
    69: "TELIA_SE",
    70: "TELIA_DK",
    71: "FIRSTNET",
    72: "IN_GEN",
    73: "IN_GEN2",
    74: "TELENOR_NO",
    75: "KPN_NL",
    76: "TMO_NL",
    77: "VF_NL",
    78: "CA_COMMON",
    79: "SASKTEL",
    80: "ORANGE_BE",
    81: "NA_COMMON",
    82: "MX_COMMON",
    83: "MY_COMMON",
    84: "VZWPRIVATE_US",
}

DL_VALUE_TO_LABEL = dict(DL_VALUE_OPTIONS)
UL_VALUE_TO_LABEL = dict(UL_VALUE_OPTIONS)
DL_LABEL_TO_VALUE = {label: value for value, label in DL_VALUE_OPTIONS}
UL_LABEL_TO_VALUE = {label: value for value, label in UL_VALUE_OPTIONS}

@dataclass
class Component:
    band: int = 1
    bwClassMimoDl: int = 32768
    bwClassMimoUl: int = 0


@dataclass
class Combo:
    components: List[Component] = field(default_factory=list)
    bcs: int = 0
    configMaskLow: int = 0
    configMaskHigh: int = 0


@dataclass
class ComboDocument:
    version: int = 0
    combos: List[Combo] = field(default_factory=list)
    bitmask: int = 0


class ParseError(ValueError):
    pass


def _extract_balanced_blocks(text: str, keyword: str) -> List[str]:
    blocks = []
    pattern = re.compile(rf"\b{re.escape(keyword)}\s*\{{")
    for match in pattern.finditer(text):
        start = match.end() - 1
        depth = 0
        for idx in range(start, len(text)):
            if text[idx] == "{":
                depth += 1
            elif text[idx] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start + 1:idx])
                    break
        else:
            raise ParseError(f"Unclosed {keyword} block")
    return blocks


def _read_int(text: str, field_name: str, default: Optional[int] = None) -> int:
    match = re.search(rf"\b{re.escape(field_name)}\s*:\s*(-?\d+)", text)
    if match:
        return int(match.group(1))
    if default is not None:
        return default
    raise ParseError(f"Missing field: {field_name}")


def parse_document(text: str) -> ComboDocument:
    version = _read_int(text, "version", 0)
    bitmask = _read_int(text, "bitmask", 0)
    combos = []

    for combo_text in _extract_balanced_blocks(text, "combos"):
        components = []
        for component_text in _extract_balanced_blocks(combo_text, "components"):
            components.append(
                Component(
                    band=_read_int(component_text, "band"),
                    bwClassMimoDl=_read_int(component_text, "bwClassMimoDl", 32768),
                    bwClassMimoUl=_read_int(component_text, "bwClassMimoUl", 0),
                )
            )

        combos.append(
            Combo(
                components=components,
                bcs=_read_int(combo_text, "bcs", 0),
                configMaskLow=_read_int(combo_text, "configMaskLow", 0),
                configMaskHigh=_read_int(combo_text, "configMaskHigh", 0),
            )
        )

    return ComboDocument(version=version, combos=combos, bitmask=bitmask)


def parse_binary_document(data: bytes) -> ComboDocument:
    cls = build_shannon_lte_message_class()
    msg = cls()
    try:
        msg.ParseFromString(data)
    except Exception as exc:
        raise ParseError(f"Could not parse binary protobuf: {exc}") from exc

    if not msg.IsInitialized():
        missing = ", ".join(msg.FindInitializationErrors())
        raise ParseError(f"Binary protobuf is missing required fields: {missing}")

    doc = ComboDocument(version=int(msg.version), bitmask=int(msg.bitmask))
    for source_combo in msg.combos:
        combo = Combo(
            bcs=int(source_combo.bcs) if source_combo.HasField("bcs") else 0,
            configMaskLow=int(source_combo.configMaskLow),
            configMaskHigh=int(source_combo.configMaskHigh),
        )
        for source_component in source_combo.components:
            combo.components.append(Component(
                band=int(source_component.band),
                bwClassMimoDl=int(source_component.bwClassMimoDl),
                bwClassMimoUl=int(source_component.bwClassMimoUl),
            ))
        doc.combos.append(combo)
    return doc


def format_binary_document(document: ComboDocument) -> bytes:
    cls = build_shannon_lte_message_class()
    msg = cls()
    msg.version = document.version
    msg.bitmask = document.bitmask
    for combo in document.combos:
        target_combo = msg.combos.add()
        target_combo.bcs = combo.bcs
        target_combo.configMaskLow = combo.configMaskLow
        target_combo.configMaskHigh = combo.configMaskHigh
        for component in combo.components:
            target_component = target_combo.components.add()
            target_component.band = component.band
            target_component.bwClassMimoDl = component.bwClassMimoDl
            target_component.bwClassMimoUl = component.bwClassMimoUl
    return msg.SerializeToString()


def format_document(document: ComboDocument) -> str:
    lines = [f"version: {document.version}"]
    for combo in document.combos:
        lines.append("combos {")
        for component in combo.components:
            lines.extend(
                [
                    "  components {",
                    f"    band: {component.band}",
                    f"    bwClassMimoDl: {component.bwClassMimoDl}",
                    f"    bwClassMimoUl: {component.bwClassMimoUl}",
                    "  }",
                ]
            )
        lines.extend(
            [
                f"  bcs: {combo.bcs}",
                f"  configMaskLow: {combo.configMaskLow}",
                f"  configMaskHigh: {combo.configMaskHigh}",
                "}",
            ]
        )
    lines.append(f"bitmask: {document.bitmask}")
    return "\n".join(lines) + "\n"


def count_direction_components(combo: Combo, field_name: str) -> int:
    cc_count_by_class = {
        "A": 1,
        "B": 2,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
    }

    total_ccs = 0

    for component in combo.components:
        raw_value = getattr(component, field_name)

        if raw_value == 0:
            continue

        class_letter, _mimo = decode_bw_class(raw_value)
        total_ccs += cc_count_by_class.get(class_letter, 1)

    return total_ccs


def decode_bw_class(value: int) -> tuple[str, int]:
    if value == 0:
        return "", 0

    base_value = value & ~1
    class_map = {
        32768: "A",
        16384: "B",
        8192: "C",
        4096: "D",
        2048: "E",
        1024: "F",
    }

    class_letter = class_map.get(base_value, f"[{value}]")
    mimo = 4 if value & 1 else 2
    return class_letter, mimo


def describe_direction_combo(combo: Combo, field_name: str) -> str:

    displayed_components = []

    for component in combo.components:
        raw_value = getattr(component, field_name)
        if raw_value == 0:
            continue

        class_letter, _mimo = decode_bw_class(raw_value)

        if class_letter == "A":
            displayed_components.append(str(component.band))
        else:
            displayed_components.append(f"{component.band}{class_letter}")

    return " + ".join(displayed_components) if displayed_components else "—"


def describe_dl_mimo(combo: Combo) -> str:
    cc_count_by_class = {
        "A": 1,
        "B": 2,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
    }

    mimo_values = []

    for component in combo.components:
        raw_value = component.bwClassMimoDl

        if raw_value == 0:
            continue

        class_letter, mimo = decode_bw_class(raw_value)
        cc_count = cc_count_by_class.get(class_letter, 1)

        mimo_values.extend([str(mimo)] * cc_count)

    return " + ".join(mimo_values) if mimo_values else "—"

def describe_bcs_mask(mask: int) -> str:
    """Display BCS indices represented by the 32-bit MSB-first mask."""
    values = [str(i) for i in range(32) if mask & (1 << (31 - i))]
    return ", ".join(values) if values else "—"


class ComboEditorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Shannon LTE CA editor V2")
        self.geometry("1320x720")
        self.minsize(1320, 720)

        self.document = ComboDocument()
        self.current_path: Optional[Path] = None
        self.selected_combo_index: Optional[int] = None
        self.selected_component_index: Optional[int] = None

        self.version_var = tk.StringVar(value="0")
        self.bitmask_var = tk.StringVar(value="0")
        self.bcs_var = tk.StringVar(value=BCS_VALUE_TO_LABEL["2147483648"])
        self.configMaskLow_var = tk.StringVar(value="18445899642336968703")
        self.configMaskHigh_var = tk.StringVar(value="2097151")
        self.band_var = tk.StringVar(value="1")
        self.dl_var = tk.StringVar(value=DL_VALUE_TO_LABEL["32768"])
        self.ul_var = tk.StringVar(value=UL_VALUE_TO_LABEL["0"])
        self.search_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")

        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self.refresh_all()

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="New", command=self.new_document, accelerator="Ctrl+N")
        file_menu.add_command(label="Import .binarypb...", command=self.import_decoded_txt, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save binary", command=self.save_binary_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        self.config(menu=menu)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)

        metadata = ttk.LabelFrame(outer, text="Information", padding=8)
        metadata.pack(fill="x", pady=(0, 10))
        ttk.Label(metadata, text="Version").grid(row=0, column=0, sticky="w")
        ttk.Entry(metadata, textvariable=self.version_var, width=18, state="readonly").grid(
            row=0, column=1, padx=(6, 20)
        )
        ttk.Label(metadata, text="Bitmask").grid(row=0, column=2, sticky="w")
        ttk.Entry(metadata, textvariable=self.bitmask_var, width=18, state="readonly").grid(
            row=0, column=3, padx=(6, 20)
        )
        ttk.Button(metadata, text="Import .binarypb", command=self.import_decoded_txt).grid(
            row=0, column=4, padx=(10, 6)
        )
        ttk.Button(metadata, text="Export .binarypb", command=self.save_binary_file).grid(
            row=0, column=5, padx=(0, 0)
        )

        paned = ttk.Panedwindow(outer, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=(0, 0, 5, 0))
        right = ttk.Frame(paned, padding=(5, 0, 0, 0))
        paned.add(left, weight=3)
        paned.add(right, weight=1)      
        self.after_idle(
            lambda: paned.sashpos(0, 910)
        )
        search_frame = ttk.Frame(left)
        search_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(search_frame, text="Search").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(search_frame, text="Clear", command=lambda: self.search_var.set("")).pack(side="left")
        self.search_var.trace_add("write", lambda *_args: self.refresh_combo_tree())

        combo_frame = ttk.LabelFrame(left, text="LTE Combos", padding=6)
        combo_frame.pack(fill="both", expand=True)

        columns = (
            "index",
            "dl_combo",
            "dl_mimo",
            "ul_combo",
            "dl_ccs",
            "ul_ccs",
            "bcs",
            "configMaskLow",
            "configMaskHigh",
        )
        self.combo_tree = ttk.Treeview(
            combo_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "index": "#",
            "dl_combo": "DL Combo",
            "dl_mimo": "DL MIMO",
            "ul_combo": "UL Combo",
            "dl_ccs": "DL CCs",
            "ul_ccs": "UL CCs",
            "bcs": "BCS",
            "configMaskLow": "Conf ID 1",
            "configMaskHigh": "Conf ID 2",
        }
        widths = {
            "index": 45,
            "dl_combo": 150,
            "dl_mimo": 150,
            "ul_combo": 80,
            "dl_ccs": 50,
            "ul_ccs": 50,
            "bcs": 80,
            "configMaskLow": 140,
            "configMaskHigh": 90,
        }
        for name in columns:
            self.combo_tree.heading(name, text=headings[name])
            self.combo_tree.column(name, width=widths[name], anchor="center")
        self.combo_tree.column("dl_combo", anchor="center")
        self.combo_tree.column("ul_combo", anchor="center")

        combo_scroll = ttk.Scrollbar(combo_frame, orient="vertical", command=self.combo_tree.yview)
        self.combo_tree.configure(yscrollcommand=combo_scroll.set)
        self.combo_tree.pack(side="left", fill="both", expand=True)
        combo_scroll.pack(side="right", fill="y")
        self.combo_tree.bind("<<TreeviewSelect>>", self.on_combo_selected)
        # Add delete key
        self.combo_tree.bind("<Delete>", self.on_delete_combo_key)

        combo_buttons = ttk.Frame(left)
        combo_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(combo_buttons, text="Add combo", command=self.add_combo).pack(side="left")
        ttk.Button(combo_buttons, text="Duplicate", command=self.duplicate_combo).pack(side="left", padx=6)
        ttk.Button(combo_buttons, text="Auto fill UL band", command=self.auto_fill_ul_band).pack(side="left", padx=(0, 6))
        ttk.Button(combo_buttons, text="Auto fill ULCA", command=self.auto_fill_ulca).pack(side="left", padx=(0, 6))
        ttk.Button(combo_buttons, text="Delete", command=self.delete_combo).pack(side="left")
        ttk.Button(combo_buttons, text="Move up", command=lambda: self.move_combo(-1)).pack(side="right")
        ttk.Button(combo_buttons, text="Move down", command=lambda: self.move_combo(1)).pack(side="right", padx=6)

        combo_editor = ttk.LabelFrame(right, text="Selected combo", padding=10)
        combo_editor.pack(fill="x")

        ttk.Label(combo_editor, text="BCS").grid(row=0, column=0, sticky="w", pady=3)
        self.bcs_combobox = ttk.Combobox(
            combo_editor,
            textvariable=self.bcs_var,
            values=[label for _value, label in BCS_VALUE_OPTIONS],
            state="readonly",
        )
        self.bcs_combobox.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=3)
        self.bcs_combobox.bind("<<ComboboxSelected>>", self.on_bcs_value_changed)

        self.config_mask_low_entry = self._labeled_entry(combo_editor, "Conf ID 1", self.configMaskLow_var, 1)
        self.config_mask_high_entry = self._labeled_entry(combo_editor, "Conf ID 2", self.configMaskHigh_var, 2)

        self.config_mask_low_entry.bind("<Return>", lambda _event: self.apply_combo_fields())
        self.config_mask_high_entry.bind("<Return>", lambda _event: self.apply_combo_fields())

        self.config_mask_low_entry.bind("<KP_Enter>", lambda _event: self.apply_combo_fields())
        self.config_mask_high_entry.bind("<KP_Enter>", lambda _event: self.apply_combo_fields())
        
        ttk.Button(combo_editor, text="Set combo fields", command=self.apply_combo_fields).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        ttk.Button(
            combo_editor,
            text="Find conf_id mapping",
            command=self.open_conf_id_mapper,
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )
        combo_editor.columnconfigure(1, weight=1)

        component_frame = ttk.LabelFrame(right, text="Band Components", padding=8)
        component_frame.pack(fill="both", expand=True, pady=(10, 0))

        component_columns = ("index", "band", "dl", "ul")
        self.component_tree = ttk.Treeview(component_frame, columns=component_columns, show="headings", height=8)
        for name, heading, width in (
            ("index", "#", 20),
            ("band", "Band", 30),
            ("dl", "DL class/MIMO", 100),
            ("ul", "UL class", 80),
        ):
            self.component_tree.heading(name, text=heading)
            self.component_tree.column(name, width=width, anchor="center")
        self.component_tree.pack(fill="both", expand=True)
        self.component_tree.bind("<<TreeviewSelect>>", self.on_component_selected)
        self.component_tree.bind("<Delete>", self.on_delete_component_key)

        component_editor = ttk.Frame(component_frame)
        component_editor.pack(fill="x", pady=(8, 0))
        self.band_entry = self._labeled_entry(component_editor, "Band", self.band_var, 0)
        self.band_entry.bind("<Return>", lambda _event: self.apply_component_fields())
        self.band_entry.bind("<KP_Enter>", lambda _event: self.apply_component_fields())

        ttk.Label(component_editor, text="DL Value").grid(
            row=1, column=0, sticky="w", pady=3
        )
        self.dl_combobox = ttk.Combobox(
            component_editor,
            textvariable=self.dl_var,
            values=[label for _value, label in DL_VALUE_OPTIONS],
            state="readonly",
        )
        self.dl_combobox.grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=3
        )

        ttk.Label(component_editor, text="UL Value").grid(
            row=2, column=0, sticky="w", pady=3
        )
        self.ul_combobox = ttk.Combobox(
            component_editor,
            textvariable=self.ul_var,
            values=[label for _value, label in UL_VALUE_OPTIONS],
            state="readonly",
        )
        self.ul_combobox.grid(
            row=2, column=1, sticky="ew", padx=(8, 0), pady=3
        )

        self.dl_combobox.bind(
            "<<ComboboxSelected>>",
            self.on_component_value_changed,
        )
        self.ul_combobox.bind(
            "<<ComboboxSelected>>",
            self.on_component_value_changed,
        )

        component_editor.columnconfigure(1, weight=1)

        component_buttons = ttk.Frame(component_frame)
        component_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(component_buttons, text="Add band", command=self.add_component).pack(side="left")
        ttk.Button(component_buttons, text="Set band", command=self.apply_component_fields).pack(side="left", padx=6)
        ttk.Button(component_buttons, text="Delete", command=self.delete_component).pack(side="left")
        ttk.Button(component_buttons, text="Move up", command=lambda: self.move_component(-1)).pack(side="right")
        ttk.Button(component_buttons, text="Move down", command=lambda: self.move_component(1)).pack(side="right", padx=6)

        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=(8, 3))
        status.pack(fill="x", side="bottom")

    @staticmethod
    def _labeled_entry(parent: ttk.Widget, label: str, variable: tk.StringVar, row: int) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3)
        return entry

    def _bind_shortcuts(self) -> None:
        self.bind_all("<Control-n>", lambda _event: self.new_document())
        self.bind_all("<Control-o>", lambda _event: self.import_decoded_txt())
        self.bind_all("<Control-s>", lambda _event: self.save_binary_file())

    @staticmethod
    def _int_value(value: str, field_name: str) -> int:
        try:
            return int(value.strip(), 10)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a decimal integer") from exc

    @staticmethod
    def _dropdown_value(
        displayed_value: str,
        label_to_value: dict[str, str],
        field_name: str,
    ) -> int:
        raw_value = label_to_value.get(displayed_value)
        if raw_value is None:
            raise ValueError(f"Select a valid {field_name} option")
        return int(raw_value)

    @staticmethod
    def _dropdown_label(
        raw_value: int,
        value_to_label: dict[str, str],
    ) -> str:
        key = str(raw_value)
        return value_to_label.get(key, key)

    def apply_document_fields(self) -> None:
        try:
            self.document.version = self._int_value(self.version_var.get(), "Version")
            self.document.bitmask = self._int_value(self.bitmask_var.get(), "Bitmask")
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.status_var.set("Document fields updated")

    def refresh_all(self, select_combo: Optional[int] = None) -> None:
        self.version_var.set(str(self.document.version))
        self.bitmask_var.set(str(self.document.bitmask))
        self.refresh_combo_tree(select_combo)
        self.refresh_component_tree()
        self.status_var.set(f"{len(self.document.combos)} combinations loaded")

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        return re.sub(r"\s+", "", value).upper()

    def _combo_row_values(self, index: int, combo: Combo) -> tuple:
        return (
            index + 1,
            describe_direction_combo(combo, "bwClassMimoDl"),
            describe_dl_mimo(combo),
            describe_direction_combo(combo, "bwClassMimoUl"),
            count_direction_components(combo, "bwClassMimoDl"),
            count_direction_components(combo, "bwClassMimoUl"),
            describe_bcs_mask(combo.bcs),
            str(combo.configMaskLow),
            str(combo.configMaskHigh),
        )

    def _combo_matches_search(
        self,
        index: int,
        combo: Combo,
        query: str,
    ) -> bool:
        if not query:
            return True

        normalized_query = self._normalize_search_text(query)
        row_values = self._combo_row_values(index, combo)

        return any(
            normalized_query in self._normalize_search_text(str(value))
            for value in row_values
        )

    def refresh_combo_tree(self, select_index: Optional[int] = None) -> None:
        for item in self.combo_tree.get_children():
            self.combo_tree.delete(item)

        query = self.search_var.get().strip()
        visible_indices = []

        for idx, combo in enumerate(self.document.combos):
            if not self._combo_matches_search(idx, combo, query):
                continue

            visible_indices.append(idx)
            self.combo_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=self._combo_row_values(idx, combo),
            )

        if not self.document.combos:
            self.selected_combo_index = None
            self.clear_combo_editor()
            return

        if not visible_indices:
            self.status_var.set(f"No combinations match: {query}")
            return

        if select_index is None:
            if self.selected_combo_index in visible_indices:
                select_index = self.selected_combo_index
            else:
                select_index = visible_indices[0]
        elif select_index not in visible_indices:
            select_index = visible_indices[0]

        self.combo_tree.selection_set(str(select_index))
        self.combo_tree.focus(str(select_index))
        self.combo_tree.see(str(select_index))
        self.selected_combo_index = select_index
        self.load_combo_editor()
        self.refresh_component_tree()

        if query:
            self.status_var.set(
                f"{len(visible_indices)} of {len(self.document.combos)} combinations shown"
            )

    def refresh_component_tree(self, select_index: Optional[int] = None) -> None:
        for item in self.component_tree.get_children():
            self.component_tree.delete(item)

        combo = self.get_selected_combo()
        if combo is None:
            self.selected_component_index = None
            self.clear_component_editor()
            return

        for idx, component in enumerate(combo.components):
            self.component_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(idx + 1, component.band, component.bwClassMimoDl, component.bwClassMimoUl),
            )

        if not combo.components:
            self.selected_component_index = None
            self.clear_component_editor()
            return

        if select_index is None:
            select_index = self.selected_component_index if self.selected_component_index is not None else 0
        select_index = max(0, min(select_index, len(combo.components) - 1))
        self.component_tree.selection_set(str(select_index))
        self.component_tree.focus(str(select_index))
        self.component_tree.see(str(select_index))
        self.selected_component_index = select_index
        self.load_component_editor()

    def on_combo_selected(self, _event=None) -> None:
        selection = self.combo_tree.selection()
        if not selection:
            return
        self.selected_combo_index = int(selection[0])
        self.selected_component_index = None
        self.load_combo_editor()
        self.refresh_component_tree()

    def on_component_selected(self, _event=None) -> None:
        selection = self.component_tree.selection()
        if not selection:
            return
        self.selected_component_index = int(selection[0])
        self.load_component_editor()

    def on_component_value_changed(self, _event=None) -> None:
        # Apply DL/UL dropdown immediately
        if self.get_selected_component() is None:
            return
        self.apply_component_fields(show_no_selection=False)

    def on_bcs_value_changed(self, _event=None) -> None:
        # Apply BCS dropdown immediately
        combo = self.get_selected_combo()
        if combo is None:
            return
        raw_value = BCS_LABEL_TO_VALUE.get(self.bcs_var.get())
        if raw_value is None:
            return
        combo.bcs = int(raw_value)
        self.refresh_combo_tree(self.selected_combo_index)
        self.status_var.set("BCS updated")

    def get_selected_combo(self) -> Optional[Combo]:
        if self.selected_combo_index is None:
            return None
        if not (0 <= self.selected_combo_index < len(self.document.combos)):
            return None
        return self.document.combos[self.selected_combo_index]

    def get_selected_component(self) -> Optional[Component]:
        combo = self.get_selected_combo()
        if combo is None or self.selected_component_index is None:
            return None
        if not (0 <= self.selected_component_index < len(combo.components)):
            return None
        return combo.components[self.selected_component_index]

    def load_combo_editor(self) -> None:
        combo = self.get_selected_combo()
        if combo is None:
            self.clear_combo_editor()
            return
        self.bcs_var.set(BCS_VALUE_TO_LABEL.get(str(combo.bcs), str(combo.bcs)))
        self.configMaskLow_var.set(str(combo.configMaskLow))
        self.configMaskHigh_var.set(str(combo.configMaskHigh))

    def clear_combo_editor(self) -> None:
        self.bcs_var.set(BCS_VALUE_TO_LABEL["2147483648"])
        self.configMaskLow_var.set("18445899642336968703")
        self.configMaskHigh_var.set("2097151")

    def load_component_editor(self) -> None:
        component = self.get_selected_component()
        if component is None:
            self.clear_component_editor()
            return
        self.band_var.set(str(component.band))
        self.dl_var.set(
            self._dropdown_label(component.bwClassMimoDl, DL_VALUE_TO_LABEL)
        )
        self.ul_var.set(
            self._dropdown_label(component.bwClassMimoUl, UL_VALUE_TO_LABEL)
        )

    def clear_component_editor(self) -> None:
        self.band_var.set("1")
        self.dl_var.set(DL_VALUE_TO_LABEL["32768"])
        self.ul_var.set(UL_VALUE_TO_LABEL["0"])

    def add_combo(self) -> None:
        combo = Combo(
            components=[Component()],
            bcs=2147483648,
            configMaskLow=18445899642336968703,
            configMaskHigh=2097151,
        )
        self.document.combos.append(combo)
        index = len(self.document.combos) - 1
        self.selected_component_index = 0
        self.refresh_combo_tree(index)
        self.refresh_component_tree(0)
        self.status_var.set("New combination added")
        
    @staticmethod
    def _copy_combo(combo: Combo) -> Combo:
        """Create an independent copy of a combo."""
        return Combo(
            components=[
                Component(
                    band=component.band,
                    bwClassMimoDl=component.bwClassMimoDl,
                    bwClassMimoUl=component.bwClassMimoUl,
                )
                for component in combo.components
            ],
            bcs=combo.bcs,
            configMaskLow=combo.configMaskLow,
            configMaskHigh=combo.configMaskHigh,
        )


    @staticmethod
    def _combo_base_signature(combo: Combo) -> tuple:
        """
        Identify combos that are identical apart from their UL settings.

        Component order is preserved because it is meaningful for repeated
        intra-band components.
        """
        return (
            tuple(
                (
                    component.band,
                    component.bwClassMimoDl,
                )
                for component in combo.components
            ),
            combo.bcs,
            combo.configMaskLow,
            combo.configMaskHigh,
        )


    @staticmethod
    def _ul_band_signature(combo: Combo) -> tuple[int, ...]:
        """
        Return the unique bands that currently have UL enabled.

        Example:
            B1 UL + B3 UL -> (1, 3)
        """
        return tuple(
            sorted({
                component.band
                for component in combo.components
                if component.bwClassMimoUl != 0
            })
        )


    @staticmethod
    def _last_dl_component_by_band(combo: Combo) -> dict[int, int]:
        """
        Return the last DL-capable component index for each unique band.

        For:
            1 + 1 + 1 + 3 + 3 + 28

        the selected indices are:
            last B1, last B3, and B28
        """
        last_indices: dict[int, int] = {}

        for index, component in enumerate(combo.components):
            if component.bwClassMimoDl == 0:
                continue

            last_indices[component.band] = index

        return last_indices


    @staticmethod
    def _set_ul_bands(
        combo: Combo,
        ul_bands: tuple[int, ...],
        ul_value: int = 32768,
    ) -> None:
        """
        Clear all existing UL values, then enable UL on the last occurrence
        of each requested band.
        """
        for component in combo.components:
            component.bwClassMimoUl = 0

        last_indices = ComboEditorApp._last_dl_component_by_band(combo)

        for band in ul_bands:
            component_index = last_indices.get(band)

            if component_index is not None:
                combo.components[component_index].bwClassMimoUl = ul_value


    def _generate_ul_variants(
        self,
        include_ulca: bool,
    ) -> None:
        selected_combo = self.get_selected_combo()

        if selected_combo is None or self.selected_combo_index is None:
            messagebox.showinfo(
                "No selection",
                "Select a combination first.",
            )
            return

        last_indices = self._last_dl_component_by_band(selected_combo)

        if not last_indices:
            messagebox.showinfo(
                "No DL bands",
                "The selected combination has no DL-capable bands.",
            )
            return

        # Component sorting
        unique_bands = list(last_indices.keys())

        requested_signatures: list[tuple[int, ...]] = []

        # Single-band UL variants e.g:
        #   1
        #   3
        #   28
        requested_signatures.extend(
            (band,)
            for band in unique_bands
        )

        if include_ulca:
            # Two-band ULCA variants:
            #   1 + 3
            #   1 + 28
            #   3 + 28
            requested_signatures.extend(
                tuple(pair)
                for pair in combinations(unique_bands, 2)
            )

        base_signature = self._combo_base_signature(selected_combo)

        """Find all already-existing UL variants of this exact DL combo,
        including the selected combo itself and variants elsewhere in
        the document."""
        existing_ul_signatures: set[tuple[int, ...]] = set()

        for combo in self.document.combos:
            if self._combo_base_signature(combo) != base_signature:
                continue

            existing_ul_signatures.add(
                self._ul_band_signature(combo)
            )

        missing_signatures = [
            signature
            for signature in requested_signatures
            if signature not in existing_ul_signatures
        ]

        if not missing_signatures:
            messagebox.showinfo(
                "Nothing to add",
                "All requested UL variants already exist.",
            )
            return

        selected_has_ul = any(
            component.bwClassMimoUl != 0
            for component in selected_combo.components
        )

        insert_at = self.selected_combo_index + 1
        created_count = 0
        modified_original = False


        if not selected_has_ul and missing_signatures:
            first_signature = missing_signatures.pop(0)

            self._set_ul_bands(
                selected_combo,
                first_signature,
            )

            existing_ul_signatures.add(first_signature)
            created_count += 1
            modified_original = True

        # Create the remaining missing variants as duplicates.
        for signature in missing_signatures:
            if signature in existing_ul_signatures:
                continue

            new_combo = self._copy_combo(selected_combo)

            self._set_ul_bands(
                new_combo,
                signature,
            )

            self.document.combos.insert(
                insert_at,
                new_combo,
            )

            insert_at += 1
            created_count += 1
            existing_ul_signatures.add(signature)

        self.selected_component_index = None
        self.refresh_combo_tree(self.selected_combo_index)
        self.refresh_component_tree()

        mode_name = (
            "UL band and ULCA"
            if include_ulca
            else "UL band"
        )

        if modified_original:
            self.status_var.set(
                f"Generated {created_count} {mode_name} variants; "
                "the selected no-UL combo was used as the first result."
            )
        else:
            self.status_var.set(
                f"Generated {created_count} new {mode_name} variants."
            )


    def auto_fill_ul_band(self) -> None:
        self._generate_ul_variants(
            include_ulca=False,
        )


    def auto_fill_ulca(self) -> None:
        self._generate_ul_variants(
            include_ulca=True,
        )

    def duplicate_combo(self) -> None:
        combo = self.get_selected_combo()
        if combo is None:
            return
        duplicate = Combo(
            components=[Component(c.band, c.bwClassMimoDl, c.bwClassMimoUl) for c in combo.components],
            bcs=combo.bcs,
            configMaskLow=combo.configMaskLow,
            configMaskHigh=combo.configMaskHigh,
        )
        insert_at = self.selected_combo_index + 1
        self.document.combos.insert(insert_at, duplicate)
        self.refresh_combo_tree(insert_at)
        self.refresh_component_tree(0)
        self.status_var.set("Combination duplicated")

    def delete_combo(self) -> None:
        if self.selected_combo_index is None:
            return
        if not messagebox.askyesno("Delete combination", "Delete the selected CA combination?"):
            return
        index = self.selected_combo_index
        del self.document.combos[index]
        self.selected_component_index = None
        self.refresh_combo_tree(min(index, len(self.document.combos) - 1))
        self.refresh_component_tree()
        self.status_var.set("Combination deleted")

    def move_combo(self, direction: int) -> None:
        if self.selected_combo_index is None:
            return
        old = self.selected_combo_index
        new = old + direction
        if not (0 <= new < len(self.document.combos)):
            return
        self.document.combos[old], self.document.combos[new] = self.document.combos[new], self.document.combos[old]
        self.refresh_combo_tree(new)
        self.status_var.set("Combination moved")

    def apply_combo_fields(self) -> None:
        combo = self.get_selected_combo()
        if combo is None:
            messagebox.showinfo("No selection", "Select or add a combination first")
            return
        try:
            raw_bcs = BCS_LABEL_TO_VALUE.get(self.bcs_var.get())
            if raw_bcs is None:
                raise ValueError("Select a valid BCS option")

            config_mask_low = self._int_value(self.configMaskLow_var.get(), "Conf ID 1")
            config_mask_high = self._int_value(self.configMaskHigh_var.get(), "Conf ID 2")

            if not 0 <= config_mask_low <= 0xFFFFFFFFFFFFFFFF:
                raise ValueError("Conf ID 1 must fit in uint64")
            if not 0 <= config_mask_high <= 0xFFFFFFFF:
                raise ValueError("Conf ID 2 must fit in uint32")

            combo.bcs = int(raw_bcs)
            combo.configMaskLow = config_mask_low
            combo.configMaskHigh = config_mask_high
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.refresh_combo_tree(self.selected_combo_index)
        self.status_var.set("Combination fields updated")

    def open_conf_id_mapper(self) -> None:
        combo = self.get_selected_combo()
        if combo is None:
            messagebox.showinfo(
                "No selection",
                "Select or add a combination first",
            )
            return

        mapper = tk.Toplevel(self)
        mapper.title("conf_id mapping")
        mapper.transient(self)
        mapper.grab_set()
        mapper.resizable(False, False)

        outer = ttk.Frame(mapper, padding=12)
        outer.pack(fill="both", expand=True)

        value_frame = ttk.LabelFrame(
            outer,
            text="Calculated values",
            padding=8,
        )
        value_frame.pack(fill="x", pady=(0, 10))

        low_value_var = tk.StringVar()
        high_value_var = tk.StringVar()

        ttk.Label(value_frame, text="Conf ID 1").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=3,
        )
        ttk.Entry(
            value_frame,
            textvariable=low_value_var,
            state="readonly",
            width=24,
        ).grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(value_frame, text="Conf ID 2").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=3,
        )
        ttk.Entry(
            value_frame,
            textvariable=high_value_var,
            state="readonly",
            width=24,
        ).grid(row=1, column=1, sticky="ew", pady=3)

        value_frame.columnconfigure(1, weight=1)

        note = ttk.Label(
            outer,
            text="Updated as of May 2026",
        )
        note.pack(anchor="w", pady=(0, 8))

        checkbox_frame = ttk.LabelFrame(
            outer,
            text="Select conf_id mapping",
            padding=8,
        )
        checkbox_frame.pack(fill="both", expand=True)

        checkbox_vars: dict[int, tk.BooleanVar] = {}

        def current_masks() -> tuple[int, int]:
            low_mask = 0
            high_mask = 0

            for conf_id, variable in checkbox_vars.items():
                if not variable.get():
                    continue

                if conf_id <= 63:
                    low_mask |= 1 << conf_id
                else:
                    high_mask |= 1 << (conf_id - 64)

            return low_mask, high_mask

        def update_values(*_args) -> None:
            low_mask, high_mask = current_masks()
            low_value_var.set(str(low_mask))
            high_value_var.set(str(high_mask))

        # 84 IDs arranged column-major into a 10-row × 9-column grid.
        # Missing names remain visible as UNMAPPED(id).
        for conf_id in range(0, 85):
            row = (conf_id) % 10
            column = (conf_id) // 10

            name = CONF_ID_NAMES.get(conf_id, f"UNMAPPED({conf_id})")
            label = f"{name} ({conf_id})" if conf_id in CONF_ID_NAMES else name

            if conf_id <= 63:
                selected = bool(combo.configMaskLow & (1 << conf_id))
            else:
                selected = bool(
                    combo.configMaskHigh & (1 << (conf_id - 64))
                )

            variable = tk.BooleanVar(value=selected)
            checkbox_vars[conf_id] = variable
            variable.trace_add("write", update_values)

            ttk.Checkbutton(
                checkbox_frame,
                text=label,
                variable=variable,
            ).grid(
                row=row,
                column=column,
                sticky="w",
                padx=(0, 12),
                pady=2,
            )

        for column in range(9):
            checkbox_frame.columnconfigure(column, weight=1)

        def apply_mapping() -> None:
            low_mask, high_mask = current_masks()

            combo.configMaskLow = low_mask
            combo.configMaskHigh = high_mask

            self.configMaskLow_var.set(str(low_mask))
            self.configMaskHigh_var.set(str(high_mask))
            self.refresh_combo_tree(self.selected_combo_index)
            self.status_var.set("conf_id mapping applied")
            mapper.destroy()

        button_frame = ttk.Frame(outer)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Apply mapping",
            command=apply_mapping,
        ).pack(side="right")
        ttk.Button(
            button_frame,
            text="Cancel",
            command=mapper.destroy,
        ).pack(side="right", padx=(0, 6))

        update_values()

        mapper.update_idletasks()
        mapper.geometry(
            f"+{self.winfo_rootx() + 40}+{self.winfo_rooty() + 40}"
        )

    def add_component(self) -> None:
        combo = self.get_selected_combo()
        if combo is None:
            messagebox.showinfo("No combination", "Add or select a combination first")
            return
        try:
            component = Component(
                band=self._int_value(self.band_var.get(), "Band"),
                bwClassMimoDl=self._dropdown_value(
                    self.dl_var.get(),
                    DL_LABEL_TO_VALUE,
                    "DL value",
                ),
                bwClassMimoUl=self._dropdown_value(
                    self.ul_var.get(),
                    UL_LABEL_TO_VALUE,
                    "UL value",
                ),
            )
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        combo.components.append(component)
        self.selected_component_index = len(combo.components) - 1
        self.refresh_component_tree(self.selected_component_index)
        self.refresh_combo_tree(self.selected_combo_index)
        self.status_var.set("Band component added")

    def apply_component_fields(self, show_no_selection: bool = True) -> None:
        component = self.get_selected_component()
        if component is None:
            if show_no_selection:
                messagebox.showinfo(
                    "No selection",
                    "Select a band component first",
                )
            return
        try:
            component.band = self._int_value(self.band_var.get(), "Band")
            component.bwClassMimoDl = self._dropdown_value(
                self.dl_var.get(),
                DL_LABEL_TO_VALUE,
                "DL value",
            )
            component.bwClassMimoUl = self._dropdown_value(
                self.ul_var.get(),
                UL_LABEL_TO_VALUE,
                "UL value",
            )
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.refresh_component_tree(self.selected_component_index)
        self.refresh_combo_tree(self.selected_combo_index)
        self.status_var.set("Band component updated")

    def delete_component(self) -> None:
        combo = self.get_selected_combo()
        if combo is None or self.selected_component_index is None:
            return
        index = self.selected_component_index
        del combo.components[index]
        self.selected_component_index = None
        self.refresh_component_tree(min(index, len(combo.components) - 1))
        self.refresh_combo_tree(self.selected_combo_index)
        self.status_var.set("Band component deleted")

    def move_component(self, direction: int) -> None:
        combo = self.get_selected_combo()
        if combo is None or self.selected_component_index is None:
            return
        old = self.selected_component_index
        new = old + direction
        if not (0 <= new < len(combo.components)):
            return
        combo.components[old], combo.components[new] = combo.components[new], combo.components[old]
        self.selected_component_index = new
        self.refresh_component_tree(new)
        self.refresh_combo_tree(self.selected_combo_index)
        self.status_var.set("Band component moved")

    def new_document(self) -> None:
        self.document = ComboDocument()
        self.current_path = None
        self.selected_combo_index = None
        self.selected_component_index = None
        self.refresh_all()
        self.title("Shannon LTE CA editor V2")

    def import_decoded_txt(self) -> None:
        filename = filedialog.askopenfilename(
            title="Import LTE capability binary protobuf",
            filetypes=[
                ("Binary protobuf", "*.binarypb"),
                ("All files", "*.*"),
            ],
        )
        if not filename:
            return

        path = Path(filename)

        if path.suffix.lower() != ".binarypb":
            messagebox.showerror(
                "Invalid file",
                "Please select a .binarypb file.",
            )
            return

        try:
            self.document = parse_binary_document(path.read_bytes())
        except (
            OSError,
            ParseError,
            ValueError,
            RuntimeError,
        ) as exc:
            messagebox.showerror("Import failed", str(exc))
            return

        self.current_path = path
        self.selected_combo_index = 0 if self.document.combos else None
        self.selected_component_index = None
        self.search_var.set("")
        self.refresh_all()
        self.title(
            f"Shannon LTE CA editor -> {self.current_path.name}"
        )
        self.status_var.set(
            f"Imported {len(self.document.combos)} combinations "
            f"from {self.current_path.name}"
        )

    def save_file(self) -> None:
        self.save_binary_file()

    def save_binary_file(self) -> None:
        if self.current_path is None:
            messagebox.showinfo(
                "No file loaded",
                "Import a .binarypb file before saving.",
            )
            return

        default_name = f"{self.current_path.stem}_mod.binarypb"

        filename = filedialog.asksaveasfilename(
            title="Export binary protobuf",
            defaultextension=".binarypb",
            initialfile=default_name,
            filetypes=[
                ("Binary protobuf", "*.binarypb"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return

        output_path = Path(filename)

        try:
            output_path.write_bytes(
                format_binary_document(self.document)
            )
        except (OSError, ValueError, RuntimeError) as exc:
            messagebox.showerror(
                "Save failed",
                str(exc),
            )
            return

        self.status_var.set(
            f"Saved binary protobuf to {output_path}"
        )

        messagebox.showinfo(
            "Saved",
            f"Binary protobuf saved as:\n{output_path}",
        )

    def _write_to_path(self, path: Path) -> None:
        try:
            path.write_text(format_document(self.document), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))
            return
        self.status_var.set(f"Saved to {path}")
        messagebox.showinfo("Saved", f"Edited file saved as:\n{path}")

    def copy_exported_text(self) -> None:
        text = format_document(self.document)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status_var.set("Exported text copied to clipboard")
        
    def on_delete_combo_key(self, _event=None) -> str:
        self.delete_combo()
        return "break"


    def on_delete_component_key(self, _event=None) -> str:
        self.delete_component()
        return "break"


if __name__ == "__main__":
    app = ComboEditorApp()
    app.mainloop()

