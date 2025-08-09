
import re, datetime
from dateparser import parse as dateparse

def calc_age(birthDate: str) -> int | None:
    dt = dateparse(birthDate)
    if not dt: return None
    today = datetime.date.today()
    years = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    return years

def extract_structured(bundle: dict) -> dict:
    p = bundle.get("patient", {})
    gender = p.get("gender")
    birth = p.get("birthDate")
    age = calc_age(birth) if birth else None
    orientation = p.get("sexualOrientation")  # optional synthetic field
    addr = p.get("address", [{}])[0] if p.get("address") else {}
    loc = {k:v for k,v in {"state":addr.get("state"), "country":addr.get("country")}.items() if v}

    conds = [c.get("code", {}).get("text", "").lower() for c in bundle.get("conditions", []) if c.get("code")]
    meds = [m.get("medicationCodeableConcept", {}).get("text", "").lower() for m in bundle.get("medications", [])]

    obs = bundle.get("observations", [])
    ecog = None
    biomarkers = set()
    for o in obs:
        code = (o.get("code", {}).get("text", "") or "").lower()
        if "ecog" in code:
            val = o.get("valueQuantity", {}).get("value") or o.get("valueString")
            try: ecog = int(str(val).strip())
            except: pass
        valstr = (o.get("valueString") or "").lower()
        for token in ["pik3ca","brca","egfr","alk","braf","flt3","esr1","msi-h","her2","pd-l1"]:
            if token in valstr:
                biomarkers.add(token.upper())

    social = bundle.get("socialHistory", {})
    smoker = social.get("smoking")
    alcohol = social.get("alcohol")
    caregiver = social.get("caregiverSupport")
    distance = social.get("travelTimeMinutes")

    return {
        "gender": gender, "age": age, "orientation": orientation,
        "conditions": conds, "meds": meds, "ecog": ecog,
        "biomarkers": sorted(biomarkers),
        "location": loc,
        "social": {"smoking":smoker, "alcohol":alcohol, "caregiverSupport":caregiver, "travelTimeMinutes":distance}
    }

def extract_from_notes(notes: str) -> dict:
    txt = (notes or "").lower()
    out = {}
    m = re.search(r"ecog\s*([0-4])", txt)
    if m: out["ecog"] = int(m.group(1))
    biomarkers = set()
    for token in ["pik3ca","brca","egfr","alk","braf","flt3","esr1","msi-h","her2","pd-l1"]:
        if token in txt: biomarkers.add(token.upper())
    if biomarkers: out["biomarkers"] = sorted(biomarkers)
    if "autoimmune" in txt: out["autoimmune_history"] = True
    ml = re.search(r"(\d+)\s+prior\s+lines", txt)
    if ml: out["prior_lines"] = int(ml.group(1))
    if "measurable disease" in txt: out["measurable_disease"] = True
    return out

def build_patient_profile(bundle: dict, notes: str) -> dict:
    s = extract_structured(bundle)
    u = extract_from_notes(notes)
    profile = s.copy()
    for k,v in u.items():
        if isinstance(v, list):
            profile[k] = sorted(set(profile.get(k, []) + v))
        else:
            profile[k] = v
    diagnosis = s["conditions"][0] if s["conditions"] else None
    profile["diagnosis_hint"] = diagnosis
    return profile

def summarize_profile(p: dict) -> str:
    bits = []
    if p.get("diagnosis_hint"): bits.append(f"Diagnosis: {p['diagnosis_hint']}")
    if p.get("age") is not None: bits.append(f"Age {p['age']}")
    if p.get("gender"): bits.append(f"Gender {p['gender']}")
    if p.get("orientation"): bits.append(f"Orientation {p['orientation']}")
    if p.get("ecog") is not None: bits.append(f"ECOG {p['ecog']}")
    if p.get("biomarkers"): bits.append("Biomarkers " + ", ".join(p["biomarkers"]))
    if p.get("meds"): bits.append("Meds " + ", ".join(p["meds"][:4]))
    loc = p.get("location") or {}
    if loc.get("state") or loc.get("country"):
        bits.append("Location " + ", ".join([v for v in [loc.get("state"), loc.get("country")] if v]))
    sh = p.get("social") or {}
    if sh.get("caregiverSupport") is not None:
        bits.append("Caregiver " + ("yes" if sh["caregiverSupport"] else "no"))
    return "; ".join(bits)
