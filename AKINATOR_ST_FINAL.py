# -*- coding: utf-8 -*-
import os, json, math, random, shutil, unicodedata, tkinter as tk
from tkinter import ttk, filedialog

DATAFILE = "stranger_dataset.json"
WELCOME_IMAGE = "st_welcome.png"
IMAGES_DIR   = "images"

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False

# Catálogo base de características específicas (sí/no)
DEFAULT_FEATURE_LIBRARY = {
    "es_policia":     "¿Es policía en Hawkins?",
    "abre_portales":  "¿Abre portales entre mundos?",
    "devora_humanos": "¿Caza o devora humanos?",
    "hermana_max":    "¿Tu personaje tiene una hermana que se llama Max?",
    "cicatrices":     "¿Tiene el cuerpo con cicatrices o aspecto deformado?",
    "boca_petalo":    "¿Tiene una boca que se abre como una flor?",
    "sombrero":       "¿Usa sombrero?",
    "sangrado_nariz": "¿Le sangra la nariz al usar poderes?",
    "tiene_poderes":  "¿Tiene superpoderes?",
}

EMPTY_DATASET = []

# Atributos que el motor puede usar
CORE_ATTRS = [
    "genero", "rol", "origen", "tiene_poderes",
    "cabello_color", "cabello_longitud", "complexion",
    "sombrero", "sangrado_nariz", "cicatrices", "boca_petalo",
    "es_policia", "abre_portales", "devora_humanos", "hermana_max"
]

PRETTY = {
    "genero":"género","rol":"rol","origen":"origen","tiene_poderes":"superpoderes",
    "cabello_color":"color de cabello","cabello_longitud":"longitud del cabello","complexion":"complexión",
    "sombrero":"sombrero","sangrado_nariz":"sangrado de nariz","cicatrices":"cicatrices o piel deformada",
    "boca_petalo":"boca en forma de flor","es_policia":"policía","abre_portales":"abre portales",
    "devora_humanos":"devora humanos","hermana_max":"tiene una hermana llamada Max"
}

# Plantillas de preguntas
QUESTION_TEMPLATES = {
    "tiene_poderes": ("¿Tiene superpoderes?", "¿Tiene superpoderes?"),
    "sombrero": ("¿Usa sombrero?", "¿Usa sombrero?"),
    "sangrado_nariz": ("¿Le sangra la nariz al usar poderes?", "¿Le sangra la nariz al usar poderes?"),
    "cicatrices": ("¿Tiene el cuerpo con cicatrices o aspecto deformado?", "¿Tiene el cuerpo con cicatrices o aspecto deformado?"),
    "boca_petalo": ("¿Tiene una boca que se abre como una flor?", "¿Tiene una boca que se abre como una flor?"),
    "es_policia": ("¿Es policía en Hawkins?", "¿Es policía en Hawkins?"),
    "abre_portales": ("¿Abre portales entre mundos?", "¿Abre portales entre mundos?"),
    "devora_humanos": ("¿Caza o devora humanos?", "¿Caza o devora humanos?"),
    "hermana_max": ("¿Tu personaje tiene una hermana que se llama Max?", "¿Tu personaje tiene una hermana que se llama Max?"),
    "genero": {"Masculino":"¿Su genero es masculino?","Femenino":"¿Su genero es femenino?","Otro":"¿Su genero es otro?"},
    "rol": {"humano":"¿Es humano?","monstruo":"¿Es un monstruo?"},
    "origen": {"Hawkins":"¿Es de Hawkins?","UpsideDown":"¿Viene del Mundo del Revés?"},
    "cabello_color": lambda v: f"¿Tiene el cabello {v}?",
    "cabello_longitud": {"corto":"¿Tiene el cabello corto?","medio":"¿Tiene el cabello medio?","largo":"¿Tiene el cabello largo?","ninguno":"¿No tiene cabello?"},
    "complexion": lambda v: f"¿Su complexión es {v}?",
}

# Parámetros del motor
PHASE_BASIC_Q = 2
PHASE_PHYS_Q  = 2
QUESTION_MIN_REVEAL = 5
QUESTION_MIN_FOR_ADD = 5
PROB_CONFIRM = 0.80
TOPK_RANDOM = 4

# ---------- Persistencia ----------
def _ensure_file():
    """Crea un JSON vacío con catálogo si no existe."""
    if not os.path.exists(DATAFILE):
        data = {"catalog": DEFAULT_FEATURE_LIBRARY.copy(), "personajes": EMPTY_DATASET}
        with open(DATAFILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def _normalize_dataset(data):
    """Normaliza atributos heredados y asegura valores por defecto."""
    cat = data.get("catalog", {}) or {}
    cat.pop("es_lider_grupo", None)
    data["catalog"] = cat
    norm = []
    for p in data.get("personajes", []):
        attrs = dict(p.get("atributos", {}))
        attrs.pop("es_lider_grupo", None)
        attrs.pop("habilidad", None)
        g = attrs.get("genero", None)
        if g in ("Hombre","Masculino","male","Male"): attrs["genero"] = "Masculino"
        elif g in ("Mujer","Femenino","female","Female"): attrs["genero"] = "Femenino"
        elif g not in ("Masculino","Femenino","Otro"): attrs["genero"] = "Otro" if g else "Otro"
        if "tiene_poderes" not in attrs: attrs["tiene_poderes"] = False
        p["atributos"] = attrs
        norm.append(p)
    data["personajes"] = norm
    return data

def read_data():
    """Lee JSON, normaliza y devuelve dict con catálogo y personajes."""
    _ensure_file()
    with open(DATAFILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data = _normalize_dataset(data)
    write_data(data)
    return data

def write_data(data):
    """Escribe JSON completo en disco."""
    with open(DATAFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_catalog():
    """Devuelve catálogo de preguntas sí/no."""
    return read_data().get("catalog", {})

def save_catalog(new_catalog):
    """Guarda catálogo (limpiando claves obsoletas)."""
    data = read_data()
    data["catalog"] = {k:v for k,v in (new_catalog or {}).items() if k != "es_lider_grupo"}
    write_data(data)

def load_dataset():
    """Devuelve lista de personajes."""
    return read_data().get("personajes", [])

def save_dataset(personajes):
    """Guarda lista de personajes."""
    data = read_data()
    data["personajes"] = personajes
    write_data(data)

def build_domains(personajes):
    """Construye dominios de valores por atributo para combos del formulario."""
    dom = {}
    for p in personajes:
        for k, v in p.get("atributos", {}).items():
            dom.setdefault(k, set()).add(v)
    for k in CORE_ATTRS:
        dom.setdefault(k, set())
    return {k: sorted(list(v), key=lambda x: str(x)) for k, v in dom.items()}

# ---------- Utilidades de inferencia ----------
def filter_candidates(personajes, hechos, negaciones):
    """Filtra personajes que cumplen hechos y no contradicen negaciones."""
    out = []
    for p in personajes:
        attrs = p.get("atributos", {})
        ok = True
        for k, v in hechos.items():
            if k in attrs and attrs[k] != v: ok = False; break
        if not ok: continue
        for (ak, av) in negaciones:
            if ak in attrs and attrs[ak] == av: ok = False; break
        if ok: out.append(p)
    return out

def is_boolean_attr(cands, attr):
    """Indica si un atributo se comporta como booleano en candidatos."""
    vals = [c.get("atributos", {}).get(attr, None) for c in cands if attr in c.get("atributos", {})]
    return len(vals) > 0 and set(type(v) for v in vals) == {bool}

def value_counts(cands, attr):
    """Cuenta valores de un atributo en candidatos."""
    cnt = {}
    for c in cands:
        if attr in c.get("atributos", {}):
            v = c["atributos"][attr]; cnt[v] = cnt.get(v, 0) + 1
    return cnt

def entropy(counts):
    """Entropía de la distribución de valores (selección de preguntas)."""
    n = sum(counts.values())
    if n == 0: return 0.0
    return -sum((c/n)*math.log2(c/n) for c in counts.values() if c>0)

def _best_from_pool(cands, hechos, asked_pairs, pool_attrs):
    """Elige la mejor pregunta dentro de un conjunto dado de atributos."""
    attrs = []
    present = set(k for c in cands for k in c.get("atributos", {}).keys())
    for a in pool_attrs:
        if a in present and a not in hechos:
            attrs.append(a)
    scored = []
    for a in attrs:
        cnt = value_counts(cands, a)
        if not cnt: continue
        h = entropy(cnt)
        if is_boolean_attr(cands, a):
            t = ('bool', a)
            if t in asked_pairs: continue
            scored.append((h, t))
        else:
            n = sum(cnt.values())
            best_t, best_worst = None, math.inf
            for v, c in cnt.items():
                t = ('cat', a, v)
                if t in asked_pairs: continue
                worst = max(c, n-c)
                if worst < best_worst: best_t, best_worst = t, worst
            if best_t: scored.append((h, best_t))
    if not scored: return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return random.choice(scored[:TOPK_RANDOM])[1]

def best_question_entropy(cands, hechos, asked_pairs, disallow_attrs=set()):
    """Pregunta general por entropía, evitando atributos ya usados."""
    attrs = set(k for c in cands for k in c.get("atributos", {}).keys())
    attrs = [a for a in attrs if a not in hechos and a not in disallow_attrs]
    scored = []
    for a in attrs:
        cnt = value_counts(cands, a)
        if not cnt: continue
        h = entropy(cnt)
        if is_boolean_attr(cands, a):
            t = ('bool', a)
            if t in asked_pairs: continue
            scored.append((h, t))
        else:
            n = sum(cnt.values())
            best_t, best_worst = None, math.inf
            for v, c in cnt.items():
                t = ('cat', a, v)
                if t in asked_pairs: continue
                worst = max(c, n-c)
                if worst < best_worst: best_t, best_worst = t, worst
            if best_t: scored.append((h, best_t))
    if not scored: return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return random.choice(scored[:TOPK_RANDOM])[1]

def score_candidate(p, hechos):
    """Puntaje de coincidencias entre un personaje y los hechos actuales."""
    attrs = p.get("atributos", {})
    return sum(1 for k, v in hechos.items() if attrs.get(k, object()) == v)

def top_two(cands, hechos):
    """Devuelve los dos mejores candidatos por puntaje."""
    scores = [(c, score_candidate(c, hechos)) for c in cands]
    scores.sort(key=lambda x: x[1], reverse=True)
    return [c for c,_ in scores[:2]]

def discriminating_question(c1, c2, hechos, asked_pairs):
    """Pregunta que diferencia a los dos mejores candidatos."""
    prefer = ["es_policia", "tiene_poderes", "hermana_max", "devora_humanos",
              "boca_petalo", "cicatrices", "sangrado_nariz",
              "genero", "origen", "rol", "cabello_color", "cabello_longitud", "complexion"]
    attrs = set(c1.get("atributos", {}).keys()) | set(c2.get("atributos", {}).keys())
    ordered = [a for a in prefer if a in attrs] + [a for a in (attrs - set(prefer))]
    for a in ordered:
        if a in hechos: continue
        va, vb = c1["atributos"].get(a, None), c2["atributos"].get(a, None)
        if va == vb or va is None or vb is None: continue
        t = ('bool', a) if is_boolean_attr([c1,c2], a) else ('cat', a, va)
        if t not in asked_pairs: return t
    return None

def candidate_probability(candidatos, hechos):
    """Estimación de probabilidad del mejor candidato."""
    if not candidatos: return None, 0.0, 0
    scores = [(c, score_candidate(c, hechos)) for c in candidatos]
    scores.sort(key=lambda x: x[1], reverse=True)
    s_sum = sum(s+1 for _, s in scores)  # suavizado
    best_c, best_s = scores[0]
    prob = (best_s + 1) / s_sum if s_sum > 0 else 0.0
    return best_c, prob, best_s

def pretty_attr(a):
    """Nombre legible de un atributo."""
    return PRETTY.get(a, a)

def question_text(q, catalog):
    """Texto de la pregunta para un tuple de pregunta."""
    if q[0] == 'bool':
        a = q[1]
        if a in catalog: return catalog[a]
        tpl = QUESTION_TEMPLATES.get(a)
        if isinstance(tpl, tuple): return tpl[0]
        return f"¿Tiene {pretty_attr(a)}?"
    else:
        _, a, v = q
        tpl = QUESTION_TEMPLATES.get(a)
        if callable(tpl): return tpl(v)
        if isinstance(tpl, dict) and v in tpl: return tpl[v]
        return f"¿Su {pretty_attr(a)} es «{v}»?"

def slugify(text):
    """Convierte a un nombre de archivo seguro."""
    t = unicodedata.normalize('NFD', text)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = ''.join(ch for ch in t if ch.isalnum() or ch in (' ', '_', '-')).strip()
    return t.lower().replace(' ', '_')

# ---------- Imágenes ----------
def find_character_image(name):
    """Busca imagen en ./images usando nombre o slug."""
    base = os.path.join(IMAGES_DIR, name)
    slug = os.path.join(IMAGES_DIR, slugify(name))
    for e in (".png",".gif",".jpg",".jpeg"):
        if os.path.exists(base+e): return base+e
        if os.path.exists(slug+e): return slug+e
    return None

def load_image_for_ui(path, max_w=360, max_h=360):
    """Carga imagen escalada para mostrar en Tk."""
    if path is None: return None
    try:
        if PIL_OK:
            im = Image.open(path); im.thumbnail((max_w,max_h), Image.LANCZOS)
            return ImageTk.PhotoImage(im)
        img = tk.PhotoImage(file=path)
        w,h = img.width(),img.height()
        fx = max(1,int(w/max_w)) if w>max_w else 1
        fy = max(1,int(h/max_h)) if h>max_h else 1
        if fx>1 or fy>1: img = img.subsample(fx, fy)
        return img
    except Exception:
        return None

# ---------- Formulario: Agregar personaje ----------
class AddCharacterForm(tk.Frame):
    """Formulario para crear un personaje y opcionalmente sumar preguntas al catálogo."""
    def __init__(self, master, dominios, prefill, theme, on_save, on_cancel, get_catalog, set_catalog):
        super().__init__(master, bg=theme["panel"])
        self.dom = dominios
        self.prefill = prefill or {}
        self.theme = theme
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.get_catalog = get_catalog
        self.set_catalog = set_catalog
        self.selected_photo = None
        self._build()

    def _combo(self, parent, values, width=18, default=""):
        cb = ttk.Combobox(parent, values=values, width=width)
        if default: cb.set(default)
        return cb

    def _build(self):
        t = self.theme
        tk.Label(self, text="Agregar personaje", bg=t["panel"], fg=t["fg"],
                 font=("Helvetica", 12, "bold")).pack(pady=(8, 4))

        canvas = tk.Canvas(self, bg=t["panel"], highlightthickness=0, height=440)
        vbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=t["panel"])
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(8,0), pady=(0,8))
        vbar.pack(side="right", fill="y", padx=(0,8), pady=(0,8))

        # Datos básicos
        basics = tk.LabelFrame(body, text="Datos básicos", bg=t["panel"], fg=t["fg"])
        basics.configure(highlightbackground="#5a1d23", highlightthickness=1)
        basics.grid(row=0, column=0, sticky="ew", padx=(0,8), pady=(0,8))
        for i in range(3): basics.columnconfigure(i, weight=1)

        tk.Label(basics, text="Nombre", bg=t["panel"], fg=t["fg"]).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.name_var = tk.StringVar()
        tk.Entry(basics, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4, columnspan=2)

        genero_vals = ["Masculino","Femenino","Otro"]
        rol_vals    = sorted(set(list(self.dom.get("rol", [])) + ["humano","monstruo"]))
        origen_vals = sorted(set(list(self.dom.get("origen", [])) + ["Hawkins","UpsideDown"]))

        def add_row(r, label, cb):
            tk.Label(basics, text=label, bg=t["panel"], fg=t["fg"]).grid(row=r, column=0, sticky="w", padx=6, pady=4)
            cb.grid(row=r, column=1, sticky="ew", padx=6, pady=4, columnspan=2)

        self.cb_genero = self._combo(basics, genero_vals)
        self.cb_rol    = self._combo(basics, rol_vals)
        self.cb_origen = self._combo(basics, origen_vals)
        add_row(1, "Género", self.cb_genero)
        add_row(2, "Rol", self.cb_rol)
        add_row(3, "Origen", self.cb_origen)

        # Foto
        tk.Label(basics, text="Foto", bg=t["panel"], fg=t["fg"]).grid(row=4, column=0, sticky="w", padx=6, pady=(4,6))
        ph_row = tk.Frame(basics, bg=t["panel"]); ph_row.grid(row=4, column=1, sticky="ew", padx=6, pady=(4,6), columnspan=2)
        self.photo_path_lbl = tk.Label(ph_row, text="(sin seleccionar)", bg=t["panel"], fg="#ffd2d2")
        ttk.Button(ph_row, text="Seleccionar…", command=self._pick_photo).pack(side="left", padx=(0,6))
        self.photo_path_lbl.pack(side="left")

        # Rasgos físicos
        phys = tk.LabelFrame(body, text="Rasgos físicos", bg=t["panel"], fg=t["fg"])
        phys.configure(highlightbackground="#5a1d23", highlightthickness=1)
        phys.grid(row=1, column=0, sticky="ew", padx=(0,8), pady=(0,8))
        for i in range(2): phys.columnconfigure(i, weight=1)

        cab_color_vals = sorted(set(list(self.dom.get("cabello_color", [])) + ["castaño","negro","rubio","pelirojo","ninguno"]))
        cab_long_vals  = sorted(set(list(self.dom.get("cabello_longitud", [])) + ["corto","medio","largo","ninguno"]))
        comp_vals      = sorted(set(list(self.dom.get("complexion", [])) + ["Delgado/a","Musculoso/a","Robusto/a","Proporcionado/a"]))

        tk.Label(phys, text="Color de cabello", bg=t["panel"], fg=t["fg"]).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.cb_cab_color = self._combo(phys, cab_color_vals); self.cb_cab_color.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        tk.Label(phys, text="Longitud de cabello", bg=t["panel"], fg=t["fg"]).grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.cb_cab_long = self._combo(phys, cab_long_vals); self.cb_cab_long.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        tk.Label(phys, text="Complexión", bg=t["panel"], fg=t["fg"]).grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.cb_complexion = self._combo(phys, comp_vals); self.cb_complexion.grid(row=2, column=1, sticky="ew", padx=6, pady=4)

        # Específicas (catálogo)
        self.feat = tk.LabelFrame(body, text="Características específicas (confirmación)", bg=t["panel"], fg=t["fg"])
        self.feat.configure(highlightbackground="#5a1d23", highlightthickness=1)
        self.feat.grid(row=2, column=0, sticky="ew", padx=(0,8), pady=(0,8))
        for i in range(4): self.feat.columnconfigure(i, weight=1)

        self.feature_rows = []
        self._build_feature_rows()

        r = self._feat_next_row
        tk.Frame(self.feat, height=1, bg="#5a1d23").grid(row=r, column=0, columnspan=4, sticky="ew", pady=6); r += 1
        tk.Label(self.feat, text="Agregar NUEVA característica (sí/no)", bg=t["panel"], fg=t["fg"],
                 font=("Helvetica", 10, "bold")).grid(row=r, column=0, columnspan=4, sticky="w", padx=6, pady=(0,4)); r += 1

        tk.Label(self.feat, text="Pregunta (sí/no)", bg=t["panel"], fg=t["fg"]).grid(row=r, column=0, sticky="w", padx=6, pady=2)
        self.new_qtext = tk.Entry(self.feat); self.new_qtext.grid(row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=2); r += 1
        tk.Label(self.feat, text="Clave (opcional, sin espacios)", bg=t["panel"], fg=t["fg"]).grid(row=r, column=0, sticky="w", padx=6, pady=2)
        self.new_key = tk.Entry(self.feat); self.new_key.grid(row=r, column=1, sticky="ew", padx=6, pady=2)
        tk.Label(self.feat, text="Valor", bg=t["panel"], fg=t["fg"]).grid(row=r, column=2, sticky="e", padx=6, pady=2)
        self.new_val = ttk.Combobox(self.feat, values=["Sí", "No"], width=8); self.new_val.set("Sí")
        self.new_val.grid(row=r, column=3, sticky="w", padx=6, pady=2); r += 1

        self.chk_add_to_catalog = tk.IntVar(value=1)
        tk.Checkbutton(self.feat, text="Añadir al catálogo global", variable=self.chk_add_to_catalog,
                       bg=t["panel"], fg=t["fg"], selectcolor=t["panel"], activebackground=t["panel"]).grid(row=r, column=0, sticky="w", padx=6, pady=2)

        self.add_msg = tk.Label(self.feat, text="", bg=t["panel"], fg="#ffb3b3")
        ttk.Button(self.feat, text="Añadir característica", command=self._ui_add_feature).grid(row=r, column=1, sticky="w", padx=6, pady=2)
        ttk.Button(self.feat, text="Refrescar catálogo", command=self._refresh_catalog).grid(row=r, column=2, sticky="w", padx=6, pady=2)
        self.add_msg.grid(row=r, column=3, sticky="w", padx=6, pady=2); r += 1

        tk.Label(self.feat, text="Nuevas añadidas:", bg=t["panel"], fg=t["fg"]).grid(row=r, column=0, sticky="w", padx=6, pady=(4,2))
        self.added_box = tk.Listbox(self.feat, height=4)
        self.added_box.grid(row=r, column=1, columnspan=3, sticky="ew", padx=6, pady=(4,2))
        self.new_features = []; r += 1

        btns = tk.Frame(self, bg=t["panel"]); btns.pack(pady=(4, 8))
        ttk.Button(btns, text="Guardar", command=self._save_click).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancelar", command=self.on_cancel).pack(side="left", padx=6)

    def _build_feature_rows(self):
        """Dibuja filas de catálogo (sí/no) en el formulario."""
        for _,_,cb in getattr(self, "feature_rows", []): cb.destroy()
        for w in getattr(self, "_feat_labels", []): w.destroy()
        self.feature_rows, self._feat_labels = [], []
        r = 0
        catalog = self.get_catalog()
        for attr, qtext in catalog.items():
            lab = tk.Label(self.feat, text=qtext, bg=self.theme["panel"], fg=self.theme["fg"])
            lab.grid(row=r, column=0, sticky="w", padx=6, pady=2)
            cb = ttk.Combobox(self.feat, values=["", "Sí", "No"], width=10)
            v = self.prefill.get(attr, None)
            if isinstance(v, bool): cb.set("Sí" if v else "No")
            cb.grid(row=r, column=1, sticky="w", padx=6, pady=2)
            self.feature_rows.append((attr, qtext, cb))
            self._feat_labels.append(lab)
            r += 1
        self._feat_next_row = r

    def _refresh_catalog(self):
        """Recarga catálogo desde disco y refresca UI."""
        self.set_catalog(load_catalog())
        self._build_feature_rows()
        self.add_msg.config(text="Catálogo actualizado.")

    def _pick_photo(self):
        """Selector de foto del personaje (copia al directorio images)."""
        path = filedialog.askopenfilename(
            title="Selecciona una foto",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.gif"), ("Todos", "*.*")]
        )
        if path:
            self.selected_photo = path
            self.photo_path_lbl.config(text=os.path.basename(path))

    def _ui_add_feature(self):
        """Añade una nueva característica sí/no al personaje (y opcionalmente al catálogo)."""
        qtxt = self.new_qtext.get().strip()
        if not qtxt:
            self.add_msg.config(text="Escribe la pregunta."); return
        key = (self.new_key.get().strip() or slugify(qtxt))
        val = (self.new_val.get().strip() == "Sí")
        existing = set(self.get_catalog().keys())
        added    = {k for k,_,_ in self.new_features}
        if key in existing or key in added:
            self.add_msg.config(text="Esa clave ya existe."); return
        self.new_features.append((key, qtxt, val))
        self.added_box.insert("end", f"{qtxt}  → {'Sí' if val else 'No'}")
        if self.chk_add_to_catalog.get() == 1:
            cat = self.get_catalog().copy(); cat[key] = qtxt
            save_catalog(cat); self.set_catalog(cat); self._build_feature_rows()
            self.add_msg.config(text="Agregada y catálogo actualizado.")
        else:
            self.add_msg.config(text="Agregada al personaje.")
        self.new_qtext.delete(0,"end"); self.new_key.delete(0,"end"); self.new_val.set("Sí")

    def _save_click(self):
        """Compila los datos del formulario y llama al callback de guardado."""
        name = self.name_var.get().strip()
        if not name:
            self.add_msg.config(text="Pon un nombre antes de guardar."); 
            return
        attrs, rules = {}, []
        if self.cb_genero.get(): attrs["genero"] = self.cb_genero.get()
        if self.cb_rol.get():    attrs["rol"]    = self.cb_rol.get()
        if self.cb_origen.get(): attrs["origen"] = self.cb_origen.get()
        if self.cb_cab_color.get(): attrs["cabello_color"] = self.cb_cab_color.get()
        if self.cb_cab_long.get():  attrs["cabello_longitud"] = self.cb_cab_long.get()
        if self.cb_complexion.get(): attrs["complexion"] = self.cb_complexion.get()
        for attr, qtext, cb in self.feature_rows:
            val = cb.get().strip()
            if val == "": continue
            b = True if val == "Sí" else False
            attrs[attr] = b
            rules.append({"attr": attr, "value": b, "question": qtext})
        raw_q = self.new_qtext.get().strip()
        if raw_q:
            key = (self.new_key.get().strip() or slugify(raw_q))
            val = (self.new_val.get().strip() == "Sí")
            exists = set(self.get_catalog().keys()) | {k for k,_,_ in self.new_features}
            if key not in exists:
                self.new_features.append((key, raw_q, val))
        for key, qtxt, val in self.new_features:
            attrs[key] = val
            rules.append({"attr": key, "value": val, "question": qtxt})
        if self.selected_photo and os.path.isfile(self.selected_photo):
            os.makedirs(IMAGES_DIR, exist_ok=True)
            ext = os.path.splitext(self.selected_photo)[1].lower()
            dst = os.path.join(IMAGES_DIR, slugify(name) + ext)
            try: shutil.copyfile(self.selected_photo, dst)
            except Exception: pass
        if self.on_save:
            self.on_save(name, attrs, rules)

# ---------- App principal ----------
class AkinatorApp(tk.Tk):
    """UI principal: flujo de preguntas, resultado y alta de personajes."""
    def __init__(self):
        super().__init__()
        self.title("Akinator — Stranger Things")
        self.geometry("720x660"); self.minsize(700, 640)

        self.theme = dict(bg="#150607", panel="#23090a", card="#2e0c0e", fg="#ffeef0",
                          accent="#e50914", accent2="#ff3b3b")
        self.configure(bg=self.theme["bg"])

        s = ttk.Style(self)
        try: s.theme_use("clam")
        except: pass
        s.configure("Root.TFrame",   background=self.theme["bg"])
        s.configure("Banner.TFrame", background=self.theme["panel"])
        s.configure("Card.TFrame",   background=self.theme["card"])
        s.configure("TLabel",        background=self.theme["bg"], foreground=self.theme["fg"])
        s.configure("Title.TLabel",  background=self.theme["panel"], foreground="#ffd2d2",
                    font=("Helvetica", 16, "bold"))
        s.configure("Q.TLabel",      background=self.theme["card"], foreground=self.theme["fg"],
                    font=("Helvetica", 13))
        s.configure("Accent.TButton", font=("Helvetica", 12, "bold"), foreground="#ffffff")
        s.map("Accent.TButton",
              background=[("!disabled", self.theme["accent"]), ("active", self.theme["accent2"])],
              foreground=[("!disabled", "#ffffff")])

        # Estado
        self.catalog    = load_catalog()
        self.personajes = load_dataset()
        self.dominios   = build_domains(self.personajes)
        self.hechos, self.negaciones = {}, set()
        self.asked_pairs, self.candidatos = set(), self.personajes[:]
        self.qtuple, self.q_count = None, 0
        self.history = []
        self.pending_confirm = None
        self.first_attrs = set()
        self.allow_add_now = False

        self.welcome_photo = self._load_welcome(WELCOME_IMAGE, max_w=650, max_h=260)
        self.root = ttk.Frame(self, style="Root.TFrame")
        self.root.pack(fill="both", expand=True, padx=16, pady=16)
        self.show_welcome()

    # --- utilidades UI ---
    def get_catalog(self): 
        """Devuelve catálogo actual en memoria."""
        return self.catalog
    def set_catalog(self, cat): 
        """Actualiza catálogo en memoria."""
        self.catalog = cat

    def _load_welcome(self, path, max_w=650, max_h=260):
        """Carga imagen de bienvenida escalada."""
        if not os.path.exists(path): return None
        try:
            if PIL_OK:
                im = Image.open(path); im.thumbnail((max_w,max_h), Image.LANCZOS)
                return ImageTk.PhotoImage(im)
            img = tk.PhotoImage(file=path); w,h = img.width(),img.height()
            fx = max(1,int(w/max_w)) if w>max_w else 1
            fy = max(1,int(h/max_h)) if h>max_h else 1
            if fx>1 or fy>1: img = img.subsample(fx, fy)
            return img
        except Exception: return None

    def _clear(self):
        """Limpia el contenedor principal."""
        for w in self.root.winfo_children(): w.destroy()

    def show_welcome(self):
        """Pantalla de bienvenida."""
        self._clear()
        banner = ttk.Frame(self.root, style="Banner.TFrame"); banner.pack(fill="x", pady=(0,10))
        if self.welcome_photo is not None:
            tk.Label(banner, image=self.welcome_photo, bg=self.theme["panel"]).pack(padx=8, pady=(8, 0))
        ttk.Label(banner, text="ADIVINARE TU PERSONAJE ¿ESTÁS LISTO?",
                  style="Title.TLabel").pack(padx=12, pady=10)
        tk.Frame(banner, height=2, bg=self.theme["accent"]).pack(side="bottom", fill="x")
        card = ttk.Frame(self.root, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=6, pady=6)
        ttk.Button(card, text="Comenzar", style="Accent.TButton", command=self.start_game).pack(pady=28)

    # --- juego ---
    def start_game(self):
        """Inicializa estado del juego y muestra pantalla de preguntas."""
        self.catalog = load_catalog()
        self.personajes = load_dataset()
        self.dominios   = build_domains(self.personajes)
        self.hechos, self.negaciones = {}, set()
        self.asked_pairs, self.candidatos = set(), self.personajes[:]
        self.qtuple, self.q_count = None, 0
        self.history = []; self.pending_confirm = None; self.first_attrs = set()
        self.allow_add_now = False
        self.show_play()
        if len(self.personajes) == 0:
            try: self.answer_btns.destroy()
            except Exception: pass
            self.set_question("Aún no hay personajes. ¿Quieres agregar el primero?")
            self.allow_add_now = True
            self.show_add_prompt()

    def show_play(self):
        """Construye la vista de preguntas."""
        self._clear()
        self.card = ttk.Frame(self.root, style="Card.TFrame"); self.card.pack(fill="both", expand=True, padx=6, pady=(6,0))
        self.lbl_q = ttk.Label(self.card, text="Piensa en un personaje de STRANGER THINGS.",
                               style="Q.TLabel", wraplength=640)
        self.lbl_q.pack(pady=(28,18))
        self.answer_btns = ttk.Frame(self.card, style="Card.TFrame"); self.answer_btns.pack()
        ttk.Button(self.answer_btns, text="Sí", style="Accent.TButton", command=lambda: self.answer(True)).grid(row=0, column=0, padx=10)
        ttk.Button(self.answer_btns, text="No", style="Accent.TButton", command=lambda: self.answer(False)).grid(row=0, column=1, padx=10)
        ttk.Button(self.answer_btns, text="No sé", style="Accent.TButton", command=lambda: self.answer(None)).grid(row=0, column=2, padx=10)
        self.photo_frame = ttk.Frame(self.card, style="Card.TFrame"); self.photo_frame.pack(pady=10)
        self.options_frame = ttk.Frame(self.card, style="Card.TFrame"); self.options_frame.pack(pady=(0,6))
        self.confirm_frame = ttk.Frame(self.card, style="Card.TFrame")
        self.bottom = ttk.Frame(self.root, style="Banner.TFrame"); self.bottom.pack(fill="x", pady=(10,0))
        tk.Frame(self.bottom, height=2, bg=self.theme["accent"]).pack(side="top", fill="x")
        inner = ttk.Frame(self.bottom, style="Banner.TFrame"); inner.pack(pady=8)
        ttk.Button(inner, text="Regresar", style="Accent.TButton", command=self.undo_last).pack(side="left", padx=8)
        ttk.Button(inner, text="Reiniciar", style="Accent.TButton", command=self.start_game).pack(side="left", padx=8)
        self.next_step()

    BASIC_SET = ["genero","rol","origen","tiene_poderes"]
    PHYS_SET  = ["cabello_color","cabello_longitud","complexion"]

    def pick_question_phased(self, cands):
        """Selecciona la siguiente pregunta por fases: básicos → físicos → específicas."""
        if self.q_count < PHASE_BASIC_Q:
            pool = [a for a in self.BASIC_SET if a not in self.first_attrs]
            random.shuffle(pool)
            q = _best_from_pool(cands, self.hechos, self.asked_pairs, pool)
            if q: return q
        if self.q_count < PHASE_BASIC_Q + PHASE_PHYS_Q:
            pool = [a for a in self.PHYS_SET if a not in self.first_attrs]
            random.shuffle(pool)
            q = _best_from_pool(cands, self.hechos, self.asked_pairs, pool)
            if q: return q
        catalog_keys = list(self.catalog.keys())
        pool = [a for a in catalog_keys + list(set(CORE_ATTRS) - set(self.BASIC_SET) - set(self.PHYS_SET))
                if a not in self.first_attrs]
        random.shuffle(pool)
        return _best_from_pool(cands, self.hechos, self.asked_pairs, pool)

    def recompute_candidates(self):
        """Recalcula candidatos filtrados."""
        self.candidatos = filter_candidates(self.personajes, self.hechos, self.negaciones)

    def set_question(self, txt):
        """Pone texto de la pregunta en pantalla."""
        self.lbl_q.config(text=txt)

    def pick_special_from_data(self, name):
        """Elige una pregunta muy distintiva guardada en el registro del personaje."""
        for p in self.personajes:
            if p.get("nombre") == name:
                for rule in p.get("confirm", []):
                    a, expected = rule["attr"], rule["value"]
                    if (a in self.hechos and self.hechos[a] == expected) or ((a, expected) in self.negaciones):
                        continue
                    q = ('bool', a) if isinstance(expected, bool) else ('cat', a, expected)
                    return q, expected, rule.get("question")
        return None, None, None

    def next_step(self):
        """Decide y muestra la siguiente pregunta o el resultado."""
        self.recompute_candidates()
        if not self.candidatos:
            try: self.answer_btns.destroy()
            except Exception: pass
            self.pending_confirm = None
            self.qtuple = None
            self.allow_add_now = True
            self.set_question("No encuentro coincidencias. ¿Deseas agregar personaje?")
            self.show_add_prompt()
            return
        if self.q_count < QUESTION_MIN_REVEAL:
            q = self.pick_question_phased(self.candidatos)
            if q is None: q = ('bool', 'tiene_poderes')
            self.qtuple = q; self.asked_pairs.add(q); self.first_attrs.add(q[1])
            self.set_question(question_text(q, self.catalog)); return
        if len(self.candidatos) == 1:
            self.present_result(self.candidatos[0]["nombre"], certain=True); return
        if self.pending_confirm is not None:
            _, q, _, txt = self.pending_confirm
            self.qtuple = q; self.set_question(txt if txt else question_text(q, self.catalog)); return
        two = top_two(self.candidatos, self.hechos)
        if len(two) == 2:
            dq = discriminating_question(two[0], two[1], self.hechos, self.asked_pairs)
            if dq is not None:
                self.qtuple = dq; self.asked_pairs.add(dq)
                self.set_question(question_text(dq, self.catalog)); return
        best, prob, _ = candidate_probability(self.candidatos, self.hechos)
        if best is not None and prob >= PROB_CONFIRM:
            q, expected, txt = self.pick_special_from_data(best["nombre"])
            if q is not None:
                self.pending_confirm = (best["nombre"], q, expected, txt)
                self.asked_pairs.add(q); self.qtuple = q
                self.set_question(txt if txt else question_text(q, self.catalog)); return
            self.present_result(best["nombre"], certain=False); return
        q = best_question_entropy(self.candidatos, self.hechos, self.asked_pairs)
        if q is None:
            if best is not None: self.present_result(best["nombre"], certain=False)
            else:
                self.allow_add_now = True
                self.set_question("No encuentro coincidencias. ¿Deseas agregar personaje?")
                self.show_add_prompt()
            return
        self.qtuple = q; self.asked_pairs.add(q)
        self.set_question(question_text(q, self.catalog))

    def answer(self, ans):
        """Registra respuesta, actualiza hechos/negaciones y continúa."""
        if not self.qtuple: return
        self.history.append((self.qtuple, ans)); self.q_count += 1
        if self.qtuple[0] == 'bool':
            a = self.qtuple[1]
            if ans is True: self.hechos[a] = True
            elif ans is False: self.negaciones.add((a, True))
        else:
            _, a, v = self.qtuple
            if ans is True: self.hechos[a] = v
            elif ans is False: self.negaciones.add((a, v))
        if self.pending_confirm is not None:
            name, q, expected, _ = self.pending_confirm
            ok = (ans is True) if q[0]=='cat' else ((expected is True and ans is True) or (expected is False and ans is False))
            self.pending_confirm = None
            if ok: self.present_result(name, certain=True); return
        self.qtuple = None; self.next_step()

    def undo_last(self):
        """Deshace la última respuesta y recomputa el estado."""
        if not self.history:
            self.set_question("No hay nada para deshacer."); return
        self.history.pop()
        self.hechos, self.negaciones = {}, set()
        self.asked_pairs, self.qtuple = set(), None
        self.q_count = 0; self.pending_confirm = None; self.first_attrs = set()
        for q, ans in self.history:
            self.asked_pairs.add(q); self.q_count += 1
            if self.q_count <= QUESTION_MIN_REVEAL: self.first_attrs.add(q[1])
            if q[0]=='bool':
                a = q[1]
                if ans is True: self.hechos[a] = True
                elif ans is False: self.negaciones.add((a, True))
            else:
                _, a, v = q
                if ans is True: self.hechos[a] = v
                elif ans is False: self.negaciones.add((a, v))
        for w in self.photo_frame.winfo_children(): w.destroy()
        for w in self.options_frame.winfo_children(): w.destroy()
        for w in self.confirm_frame.winfo_children(): w.destroy()
        self.set_question("Respuesta anterior deshecha."); self.next_step()

    def present_result(self, nombre, certain=True):
        """Muestra resultado (nombre e imagen) y opciones Sí/Intentar/No."""
        try: self.answer_btns.destroy()
        except: pass
        try: self.bottom.destroy()
        except: pass
        for w in self.photo_frame.winfo_children(): w.destroy()
        for w in self.options_frame.winfo_children(): w.destroy()
        for w in self.confirm_frame.winfo_children(): w.destroy()
        msg = f"🎯 Personaje: «{nombre}». ¿Acerté?" if certain else f"Mi mejor respuesta: «{nombre}». ¿Acerté?"
        self.set_question(msg)
        path = find_character_image(nombre)
        img  = load_image_for_ui(path)
        if img is not None:
            tk.Label(self.photo_frame, image=img, bg=self.theme["card"]).pack()
            self.photo_frame.image = img
        else:
            tk.Label(self.photo_frame, text=f"(Agrega la foto en ./images/{slugify(nombre)}.png|jpg|gif)",
                     bg=self.theme["card"], fg="#ffd2d2").pack()
        ttk.Button(self.options_frame, text="Sí", style="Accent.TButton",
                   command=lambda: self.set_question(f"¡Listo! Era «{nombre}».")).pack(side="left", padx=6)
        ttk.Button(self.options_frame, text="Intentar de nuevo", style="Accent.TButton",
                   command=self.start_game).pack(side="left", padx=6)
        ttk.Button(self.options_frame, text="No", style="Accent.TButton",
                   command=self.after_reveal_no).pack(side="left", padx=6)

    def after_reveal_no(self):
        """Pregunta si desea agregar el personaje tras fallar el resultado."""
        self.set_question("¿Deseas agregar personaje?")
        self.allow_add_now = True
        self.show_add_prompt()

    def show_add_prompt(self):
        """Muestra opciones para abrir formulario de alta."""
        if hasattr(self, "answer_btns"):
            try: self.answer_btns.destroy()
            except Exception: pass
        for w in self.confirm_frame.winfo_children(): w.destroy()
        self.confirm_frame.pack(pady=6)
        row = ttk.Frame(self.confirm_frame, style="Card.TFrame"); row.pack()
        ttk.Button(row, text="Sí", style="Accent.TButton",
                   command=self.show_add_form_gate).pack(side="left", padx=6)
        ttk.Button(row, text="No", style="Accent.TButton",
                   command=lambda: self.set_question("Ok. Usa 'Intentar de nuevo' para otra partida.")
                   ).pack(side="left", padx=6)

    def show_add_form_gate(self):
        """Controla si ya se puede abrir el formulario de alta."""
        if not self.allow_add_now and self.q_count < QUESTION_MIN_FOR_ADD and len(self.personajes) > 0:
            faltan = QUESTION_MIN_FOR_ADD - self.q_count
            self.set_question(f"Aún faltan {faltan} pregunta(s) antes de poder agregar.")
            return
        self.allow_add_now = False
        self.set_question("Completa los datos del nuevo personaje.")
        self.render_add_panel(prefill=self.hechos)

    def render_add_panel(self, prefill=None):
        """Monta el formulario de alta dentro de la tarjeta central."""
        for w in self.confirm_frame.winfo_children(): w.destroy()
        for w in self.photo_frame.winfo_children(): w.destroy()
        for w in self.options_frame.winfo_children(): w.destroy()
        form = AddCharacterForm(
            self.card, dominios=self.dominios, prefill=prefill or {},
            theme={"panel": self.theme["panel"], "fg": self.theme["fg"]},
            on_save=self.save_new_character, on_cancel=self.start_game,
            get_catalog=self.get_catalog, set_catalog=self.set_catalog
        )
        form.pack(fill="both", padx=8, pady=8)

    def save_new_character(self, name, attrs, confirm_rules):
        """Guarda un nuevo personaje en el JSON y reinicia la partida."""
        if not name:
            self.set_question("Escribe un nombre para guardar."); return
        nuevo = {"nombre": name, "atributos": attrs}
        if confirm_rules: nuevo["confirm"] = confirm_rules
        personajes = load_dataset(); personajes.append(nuevo); save_dataset(personajes)
        self.dominios = build_domains(personajes)
        self.set_question(f"Se agregó «{name}». Iniciando nueva partida…")
        self.after(650, self.start_game)

# ---------- Ejecución ----------
if __name__ == "__main__":
    os.makedirs(IMAGES_DIR, exist_ok=True)
    app = AkinatorApp()
    app.mainloop()
