import json
import os
import re
from pathlib import Path


def strip_comments(text: str) -> str:
    # remove /* ... */ and // ... comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//.*$', '', text, flags=re.M)
    return text


def recursive_find_first(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            res = recursive_find_first(v, key)
            if res is not None:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = recursive_find_first(item, key)
            if res is not None:
                return res
    return None


def recursive_find_all(obj, key):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                found.append(v)
            found.extend(recursive_find_all(v, key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(recursive_find_all(item, key))
    return found


def extract_from_blueprint(data: dict, filename: str) -> dict:
    name = Path(filename).stem

    # basic fields
    result = {
        "name": name,
        "designation": None,
        "image": f"../Images/tanks/{name}.png",
        "armaments": [],
        "rotation": None,
        "vertical": None,
        "azimuth": None,
        "reload": None,
        "penetration": None,
        "crew": None,
        "mass": None,
        "hp": None,
        "maxSpeed": None,
        "engine": None,
        "era": None,
    }

    # Mass from header.mass (assumed kilograms)
    header = data.get('header', {}) if isinstance(data, dict) else {}
    mass_val = header.get('mass')
    if mass_val is not None:
        try:
            mass_t = float(mass_val) / 1000.0
            result['mass'] = f"{mass_t:.2f}t"
        except Exception:
            pass

    # Armaments: look in top-level 'blueprints' array for type == 'cannon'
    bps = data.get('blueprints', []) if isinstance(data, dict) else []
    for bp in bps:
        try:
            if bp.get('type') == 'cannon':
                blueprint = bp.get('blueprint', {})
                cname = blueprint.get('name') or blueprint.get('displayName') or ''
                calib = blueprint.get('caliber')
                breech = blueprint.get('breechLength')
                if calib is not None and breech is not None:
                    arm = f"{calib}x{breech}mm {cname}".strip()
                else:
                    arm = cname
                if arm:
                    result['armaments'].append(arm)
        except Exception:
            continue

    # Vertical: look for type == 'layingDrive' and try nested locations
    for bp in bps:
        if bp.get('type') == 'layingDrive':
            blueprint = bp.get('blueprint', {}) or {}
            mn = None
            mx = None
            if isinstance(blueprint, dict):
                mn = blueprint.get('min')
                mx = blueprint.get('max')
                # nested under 'elevation' (common in files)
                elev = blueprint.get('elevation')
                if isinstance(elev, dict):
                    mn = elev.get('min', mn)
                    mx = elev.get('max', mx)
                # some files may use numeric fields under nested dicts with different keys
                # try shallow recursive lookup as a last resort
                if mn is None or mx is None:
                    mn = mn or recursive_find_first(blueprint, 'min')
                    mx = mx or recursive_find_first(blueprint, 'max')
            if mn is not None and mx is not None:
                try:
                    mn_f = float(mn)
                    mx_f = float(mx)
                    result['vertical'] = f"-{abs(mn_f)} / {mx_f}deg"
                except Exception:
                    result['vertical'] = f"-{mn} / {mx}deg"

            # also check azimuth and include if either min or max > 0
            az_min = None
            az_max = None
            az_obj = None
            if isinstance(blueprint, dict):
                az_obj = blueprint.get('azimuth') or recursive_find_first(blueprint, 'azimuth')
            if isinstance(az_obj, dict):
                az_min = az_obj.get('min')
                az_max = az_obj.get('max')
            # attempt to parse and include when > 0
            try:
                az_min_f = float(az_min) if az_min is not None else None
            except Exception:
                az_min_f = None
            try:
                az_max_f = float(az_max) if az_max is not None else None
            except Exception:
                az_max_f = None

            if (az_min_f is not None and az_min_f > 0) or (az_max_f is not None and az_max_f > 0):
                # format available values; use numeric formatting when possible
                a_min_str = f"{az_min_f}" if az_min_f is not None else (str(az_min) if az_min is not None else "")
                a_max_str = f"{az_max_f}" if az_max_f is not None else (str(az_max) if az_max is not None else "")
                result['azimuth'] = f"{a_min_str} / {a_max_str}deg".strip()

            # break after handling first layingDrive
            break

    # If no layingDrive provided vertical, fallback to a turret with limited rotation
    if result.get('vertical') is None:
        for bp in bps:
            try:
                if bp.get('type') == 'turret':
                    blueprint = bp.get('blueprint', {}) or {}
                    minr = blueprint.get('minRot')
                    maxr = blueprint.get('maxRot')
                    if minr is None or maxr is None:
                        continue
                    try:
                        min_f = float(minr)
                        max_f = float(maxr)
                    except Exception:
                        continue
                    # ignore full 360-style turrets (180 / -180)
                    if not (abs(max_f - 180.0) < 1e-6 and abs(min_f + 180.0) < 1e-6):
                        # use turret rot range as vertical values
                        result['vertical'] = f"{min_f} / {max_f}deg"
                        break
            except Exception:
                continue

    # Crew: count blueprints entries type == 'crewSeat'
    crew_count = sum(1 for bp in bps if bp.get('type') == 'crewSeat')
    if crew_count == 0:
        # fallback: count appearance in objects list
        objs = data.get('objects', []) if isinstance(data, dict) else []
        crew_count = sum(1 for o in objs if 'crewSeat' in o)
    if crew_count:
        result['crew'] = crew_count

    # HP: compute from maxInputTorque and targetMaxRPM if present anywhere
    torque = recursive_find_first(data, 'maxInputTorque')
    rpm = recursive_find_first(data, 'targetMaxRPM')
    if torque is None:
        torque = recursive_find_first(data, 'maxTorque')
    if rpm is None:
        rpm = recursive_find_first(data, 'maxRPM')
    try:
        if torque is not None and rpm is not None:
            torque_f = float(torque)
            rpm_f = float(rpm)
            hp = torque_f * rpm_f / 7127.0
            result['hp'] = int(round(hp))
    except Exception:
        pass

    # Engine: cylinders and cylinderDisplacement
    cylinders = recursive_find_first(data, 'cylinders')
    displacement = recursive_find_first(data, 'cylinderDisplacement')
    try:
        if cylinders is not None and displacement is not None:
            cyl_i = int(cylinders)
            disp_f = float(displacement)
            # if displacement looks large (>10) assume it's cc -> convert to liters
            if disp_f > 10:
                liters = disp_f / 1000.0
            else:
                liters = disp_f
            result['engine'] = f"{liters:.2f}L V{cyl_i}"
    except Exception:
        pass

    # Reload if present anywhere
    reload_v = recursive_find_first(data, 'reload')
    if reload_v is not None:
        result['reload'] = str(reload_v)

    # Some fields explicitly left null per spec: designation, rotation, penetration, maxSpeed, era

    return result


def process_folder(bp_folder: str, out_path: str):
    bp_folder = Path(bp_folder)
    if not bp_folder.exists() or not bp_folder.is_dir():
        print(f"Blueprint folder not found: {bp_folder}")
        return


    results = []
    for p in sorted(bp_folder.glob('*.blueprint')):
        text = p.read_text(encoding='utf-8')
        text_clean = strip_comments(text)
        try:
            data = json.loads(text_clean)
        except Exception as e:
            # try to recover by wrapping as JSON (some bp files might be JS-like)
            print(f"Failed to parse {p.name}: {e}")
            continue

        entry = extract_from_blueprint(data, p.name)
        results.append(entry)

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open('w', encoding='utf-8') as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(results)} entries to {out_file}")


def main():
    print('Blueprint -> tanks.json converter')
    default_folder = input('Blueprint folder (default: misc): ').strip() or 'misc'
    default_out = input('Output JSON path (default: Scripts/bulkConvertedFiles.json): ').strip()
    if not default_out:
        default_out = f"Scripts/bulkConvertedFiles.json"

    process_folder(default_folder, default_out)


if __name__ == '__main__':
    main()
