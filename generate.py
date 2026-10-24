import csv
import os
from collections import defaultdict

# Поточний рік (для розрахунку віку моделі)
CURRENT_YEAR = 2026

# Створюємо папку для сайту
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Читаємо шаблон HTML для моделей
with open("template.html", "r", encoding="utf-8") as f:
    template_content = f.read()

# Групуємо дані з cars.csv по моделях та роках
models_data = defaultdict(list)

with open("cars.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row["make"], row["model"], row["year"])
        models_data[key].append(row)


# ============================================================
#  ДОПОМІЖНІ ДАНІ ТА ФУНКЦІЇ ДЛЯ УНІКАЛЬНОГО КОНТЕНТУ
# ============================================================

# Тип кузова / сегмент для кожної моделі (використовується для підбору порад)
MODEL_INFO = {
    "F-150": ("full-size pickup truck", "truck"),
    "Explorer": ("three-row midsize SUV", "suv"),
    "Mustang": ("sport coupe", "sport"),
    "Maverick": ("compact pickup truck", "truck"),
    "Escape": ("compact SUV", "suv"),
    "Bronco": ("off-road-focused SUV", "suv"),
    "Bronco Sport": ("compact crossover SUV", "suv"),
    "Edge": ("two-row midsize crossover SUV", "suv"),
    "Ranger": ("midsize pickup truck", "truck"),
    "Camry": ("midsize sedan", "car"),
    "RAV4": ("compact SUV", "suv"),
    "Tacoma": ("midsize pickup truck", "truck"),
    "Tundra": ("full-size pickup truck", "truck"),
    "Highlander": ("three-row midsize SUV", "suv"),
    "Grand Highlander": ("three-row large SUV", "suv"),
    "Corolla": ("compact sedan", "car"),
    "Sienna": ("minivan", "van"),
    "4Runner": ("body-on-frame midsize SUV", "suv"),
    "Prius": ("hybrid hatchback", "car"),
    "Civic": ("compact car", "car"),
    "CR-V": ("compact SUV", "suv"),
    "Accord": ("midsize sedan", "car"),
    "Pilot": ("three-row SUV", "suv"),
    "Odyssey": ("minivan", "van"),
    "HR-V": ("subcompact crossover SUV", "suv"),
    "Passport": ("two-row midsize SUV", "suv"),
    "Ridgeline": ("midsize pickup truck", "truck"),
    "Silverado 1500": ("full-size pickup truck", "truck"),
    "Equinox": ("compact SUV", "suv"),
    "Tahoe": ("full-size SUV", "suv"),
    "Suburban": ("extended full-size SUV", "suv"),
    "Camaro": ("sport coupe", "sport"),
    "Colorado": ("midsize pickup truck", "truck"),
    "Trax": ("subcompact crossover SUV", "suv"),
}

# Поради залежно від типу автомобіля
TYPE_TIPS = {
    "truck": "Pickups see wide swings in load. A pressure that suits an empty bed may not suit a heavy payload or a trailer, so check your owner's manual and the door-jamb placard for any loaded-vehicle figure before a heavy trip.",
    "suv": "SUVs regularly carry a full cabin, luggage and sometimes a roof box or a trailer. Re-check the pressure before long trips with a full load, and always measure with the tires cold.",
    "sport": "Sport-oriented cars are sensitive to pressure: too low dulls steering response and overheats the sidewalls, too high reduces grip. Use the placard value for road driving and ask a performance-driving specialist about any track-day adjustments.",
    "van": "Minivans often run fully loaded with passengers and cargo. Check the pressure before family road trips, because a full cabin plus luggage puts the tires under the most stress on hot highway days.",
    "car": "Passenger cars lose small amounts of air every month without any visible sign. A quick monthly check with a reliable gauge keeps fuel economy, braking and tire wear on target.",
}

# Ключові слова в назвах комплектацій
OFFROAD_WORDS = ["Off-Road", "Raptor", "Tremor", "ZR2", "Trail Boss", "Badlands",
                 "Trailhunter", "TRD Pro", "Rugged", "Sasquatch", "Z71", "Timberline"]
PERFORMANCE_WORDS = ["Type R", "Dark Horse", "ZL1", "SS V8", "Performance", "Raptor", "Si Sport"]


def make_file_name(year, make, model):
    # Та сама формула, що й раніше - назви файлів не змінюються
    return f"{year}-{make.lower()}-{model.lower().replace(' ', '-')}.html"


def article(text):
    return "an" if text[0].lower() in "aeiou" else "a"


def psi_to_kpa(psi):
    return int(round(psi * 6.89476))


def psi_to_bar(psi):
    return psi * 0.0689476


def pressure_label(psi):
    return f"{psi} PSI / {psi_to_kpa(psi)} kPa / {psi_to_bar(psi):.2f} bar"


def parse_tire_size(size):
    # Приклад: 275/65R18 або 265/30ZR19 -> (275, 65, 18)
    try:
        width_part, rest = size.split("/")
        r_index = rest.index("R")
        aspect = int(rest[:r_index].replace("Z", ""))
        rim = int(rest[r_index + 1:])
        width = int(width_part)
        return width, aspect, rim
    except (ValueError, IndexError):
        return None


def tire_dimensions(size, width, aspect, rim):
    # Розрахунок за номінальним розміром шини
    sidewall_mm = width * aspect / 100
    diameter_in = rim + 2 * sidewall_mm / 25.4
    diameter_mm = diameter_in * 25.4
    revs_per_mile = 63360 / (3.14159265 * diameter_in)
    return {
        "size": size,
        "width": width,
        "aspect": aspect,
        "rim": rim,
        "sidewall_mm": sidewall_mm,
        "sidewall_in": sidewall_mm / 25.4,
        "diameter_in": diameter_in,
        "diameter_mm": diameter_mm,
        "revs": revs_per_mile,
    }


# Попередньо збираємо список сторінок по моделях (для внутрішніх посилань)
pages_by_model = defaultdict(list)
for (mk, md, yr) in models_data.keys():
    pages_by_model[(mk, md)].append((yr, make_file_name(yr, mk, md)))


def build_meta_description(make, model, year, rows):
    sizes = []
    for r in rows:
        if r["tire_size"] not in sizes:
            sizes.append(r["tire_size"])
    pairs = set((int(r["front_psi"]), int(r["rear_psi"])) for r in rows)
    if len(pairs) == 1:
        front, rear = list(pairs)[0]
        pressure = f"{front} PSI front / {rear} PSI rear"
    else:
        all_psi = [int(r["front_psi"]) for r in rows] + [int(r["rear_psi"]) for r in rows]
        pressure = f"{min(all_psi)}-{max(all_psi)} PSI depending on trim"
    sizes_text = ", ".join(sizes[:3])
    return f"{year} {make} {model} recommended cold tire pressure: {pressure}. OEM tire sizes: {sizes_text}. PSI, kPa and bar by trim."


def build_extra_content(make, model, year, rows):
    seed = sum(ord(c) for c in f"{make}{model}{year}")
    desc, category = MODEL_INFO.get(model, ("vehicle", "car"))
    age = CURRENT_YEAR - int(year)
    n = len(rows)
    n_text = "1 trim and wheel combination" if n == 1 else f"{n} trim and wheel combinations"
    full_name = f"{year} {make} {model}"

    fronts = [int(r["front_psi"]) for r in rows]
    rears = [int(r["rear_psi"]) for r in rows]
    all_psi = fronts + rears
    min_psi, max_psi = min(all_psi), max(all_psi)
    staggered = any(f != r for f, r in zip(fronts, rears))

    # Унікальні розміри шин у порядку появи
    sizes = []
    for r in rows:
        if r["tire_size"] not in sizes:
            sizes.append(r["tire_size"])

    dims = []
    for s in sizes:
        parsed = parse_tire_size(s)
        if parsed:
            dims.append(tire_dimensions(s, parsed[0], parsed[1], parsed[2]))
        else:
            print(f"Увага: не вдалося розібрати розмір шини '{s}' ({full_name})")

    rims = sorted(set(d["rim"] for d in dims))

    # ---------- Вступ ----------
    intros = [
        f"The {full_name} is {article(desc)} {desc}. Below you will find the factory-recommended cold tire pressure for {n_text}, together with a breakdown of what each tire size means in real-world dimensions.",
        f"Looking for the right air pressure for your {full_name}? This {desc} is listed here with {n_text}, and the correct cold PSI depends on which one you have. Figures are given per trim and wheel size.",
        f"Correct inflation matters on any {desc}, and the {full_name} is no exception. This guide covers {n_text} with front and rear PSI, metric conversions and calculated tire dimensions.",
    ]
    intro = intros[seed % len(intros)]

    if min_psi == max_psi and not staggered:
        pressure_sentence = f"Every version listed here calls for {min_psi} PSI cold on both axles, so there is only one number to remember."
    elif staggered:
        pressure_sentence = f"Pressure ranges from {min_psi} to {max_psi} PSI, and at least one version specifies different front and rear values, so do not assume the same figure for all four tires."
    else:
        pressure_sentence = f"Pressure ranges from {min_psi} to {max_psi} PSI depending on trim and wheel size, so match the figure to your exact version."

    if len(rims) == 1:
        rim_sentence = f"This model year is listed with {rims[0]}-inch wheels."
    elif len(rims) > 1:
        rim_sentence = f"Wheel sizes in this guide range from {rims[0]}-inch to {rims[-1]}-inch, and the recommended pressure can change with the wheel and tire package."
    else:
        rim_sentence = ""

    html = []
    html.append('<section class="extra-content">')
    html.append("""<style>
.extra-content { margin-top: 2rem; }
.extra-content h2 { margin-top: 2rem; }
.extra-content .table-scroll { overflow-x: auto; }
.extra-content table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.extra-content th, .extra-content td { border: 1px solid #cbd5e1; padding: 0.6rem; text-align: left; }
.extra-content th { background: #f1f5f9; }
</style>""")
    html.append(f"<h2>About the {full_name}</h2>")
    html.append(f"<p>{intro}</p>")
    html.append(f"<p>{pressure_sentence} {rim_sentence}</p>")

    # ---------- Таблиця PSI / kPa / bar ----------
    html.append(f"<h2>{full_name} Tire Pressure in PSI, kPa and Bar</h2>")
    html.append("<p>The same factory cold pressure converted to metric units, for gauges and gas-station pumps that use kPa or bar.</p>")
    html.append('<div class="table-scroll"><table>')
    html.append("<thead><tr><th>Trim</th><th>Front</th><th>Rear</th></tr></thead><tbody>")
    for r in rows:
        f_psi = int(r["front_psi"])
        r_psi = int(r["rear_psi"])
        html.append(f"<tr><td><strong>{r['trim']}</strong></td><td>{pressure_label(f_psi)}</td><td>{pressure_label(r_psi)}</td></tr>")
    html.append("</tbody></table></div>")

    # ---------- Розміри шин ----------
    if dims:
        html.append(f"<h2>Tire Size Breakdown for the {full_name}</h2>")
        html.append('<div class="table-scroll"><table>')
        html.append("<thead><tr><th>Tire size</th><th>Section width</th><th>Sidewall height</th><th>Rim</th><th>Overall diameter</th><th>Revolutions per mile</th></tr></thead><tbody>")
        for d in dims:
            html.append(
                f"<tr><td><strong>{d['size']}</strong></td>"
                f"<td>{d['width']} mm</td>"
                f"<td>{d['sidewall_mm']:.0f} mm ({d['sidewall_in']:.1f} in)</td>"
                f"<td>{d['rim']} in</td>"
                f"<td>{d['diameter_in']:.1f} in ({d['diameter_mm']:.0f} mm)</td>"
                f"<td>{d['revs']:.0f}</td></tr>"
            )
        html.append("</tbody></table></div>")

        first = dims[0]
        read_text = (
            f"How to read {first['size']}: {first['width']} is the section width in millimeters, "
            f"{first['aspect']} means the sidewall height is {first['aspect']}% of that width "
            f"(about {first['sidewall_mm']:.0f} mm), R marks radial construction, and {first['rim']} is the wheel diameter in inches."
        )
        if "ZR" in first["size"]:
            read_text += " The Z in ZR denotes a high-speed-capable radial."
        html.append(f"<p>{read_text}</p>")

        if len(dims) > 1:
            smallest = min(dims, key=lambda x: x["diameter_in"])
            largest = max(dims, key=lambda x: x["diameter_in"])
            diff = largest["diameter_in"] - smallest["diameter_in"]
            pct = diff / smallest["diameter_in"] * 100
            html.append(
                f"<p>The smallest tire listed ({smallest['size']}) stands about {smallest['diameter_in']:.1f} in tall, "
                f"while the largest ({largest['size']}) stands about {largest['diameter_in']:.1f} in, "
                f"a difference of {diff:.1f} in ({pct:.1f}%). Different trims are not automatically interchangeable: "
                f"if you change tire size, keeping the overall diameter within roughly 3% of the original is commonly recommended "
                f"to keep the speedometer and stability systems accurate, and a tire shop should confirm the load rating and pressure.</p>"
            )
        html.append("<p><em>Dimensions are calculated from the nominal size designation. Actual measurements vary by tire manufacturer, model and rim width.</em></p>")

    # ---------- Поради ----------
    tips = []
    tips.append(TYPE_TIPS[category])
    tips.append("Check pressure when the tires are cold: before driving, or after the vehicle has been parked for at least three hours.")
    tips.append("Your tire pressure monitoring system (TPMS) typically warns only when pressure falls around 25% below the recommended value, so it does not replace a regular manual check.")

    if any("Hybrid" in r["trim"] for r in rows):
        tips.append("On hybrids, correct pressure helps keep rolling resistance low, which supports the fuel economy the powertrain is designed to deliver.")
    if any(any(w in r["trim"] for w in OFFROAD_WORDS) for r in rows):
        tips.append("Off-road trims are often driven with reduced pressure on trails, but the figures above are for normal road use. Re-inflate to the listed pressure before returning to pavement.")
    if any(any(w in r["trim"] for w in PERFORMANCE_WORDS) for r in rows):
        tips.append("Performance trims run hotter in spirited driving, so pressure readings climb after a drive. Always set pressure cold, not right after a fast run.")
    if staggered:
        tips.append("Front and rear pressures differ on at least one version of this vehicle, so set each axle separately instead of using one value for all four tires.")
    if age >= 6:
        tips.append(f"This is a {age}-year-old model year, so the tires on it have probably been replaced. If the new tires are a different size or load rating from the sizes above, confirm the correct pressure with a tire shop.")

    html.append(f"<h2>Tire Care Tips for the {full_name}</h2>")
    html.append("<ul>")
    for t in tips:
        html.append(f"<li>{t}</li>")
    html.append("</ul>")

    # ---------- FAQ ----------
    pairs = [(int(r["front_psi"]), int(r["rear_psi"])) for r in rows]
    if len(set(pairs)) == 1:
        f_psi, r_psi = pairs[0]
        a1 = f"For every version listed, the recommended cold pressure is {f_psi} PSI front ({psi_to_kpa(f_psi)} kPa) and {r_psi} PSI rear ({psi_to_kpa(r_psi)} kPa)."
    else:
        parts = []
        for r in rows:
            parts.append(f"{r['trim']}: {r['front_psi']} PSI front / {r['rear_psi']} PSI rear")
        a1 = "It depends on the trim. " + "; ".join(parts) + "."

    sizes_text = ", ".join(sizes)
    ref_psi = fronts[0]
    low_est = ref_psi - 4
    high_est = ref_psi - 3

    html.append(f"<h2>{full_name} Tire Pressure FAQ</h2>")
    html.append(f"<h3>What is the recommended tire pressure for the {full_name}?</h3>")
    html.append(f"<p>{a1}</p>")
    html.append(f"<h3>What tire sizes does the {full_name} use?</h3>")
    html.append(f"<p>The sizes listed for this model year are {sizes_text}. The size is printed on the sidewall of your tire, so compare it with the table above to find your trim.</p>")
    html.append("<h3>Should I inflate to the maximum pressure printed on the tire?</h3>")
    html.append(f"<p>No. The number on the sidewall is the maximum the tire can safely hold, not the pressure recommended for your vehicle. Use the {min_psi}-{max_psi} PSI range from the table above or the placard on your door jamb instead.</p>" if min_psi != max_psi else f"<p>No. The number on the sidewall is the maximum the tire can safely hold, not the pressure recommended for your vehicle. Use the {min_psi} PSI from the table above or the placard on your door jamb instead.</p>")
    html.append("<h3>How much does cold weather change my tire pressure?</h3>")
    html.append(f"<p>As a rule of thumb, tire pressure drops by about 1 PSI for every 10°F (about 5.5°C) drop in temperature. A tire set to {ref_psi} PSI at around 68°F can read roughly {low_est}-{high_est} PSI after a night at 32°F, so check pressure more often in winter.</p>")
    if age >= 6:
        html.append("<h3>Is this pressure still correct if I replaced my tires?</h3>")
        html.append("<p>If the replacement tires are the same size and load rating as the original ones, the placard pressure still applies. If you changed size or load rating, ask the tire shop to confirm the right pressure.</p>")

    # ---------- Внутрішні посилання ----------
    other_years = sorted(
        [p for p in pages_by_model[(make, model)] if p[0] != year],
        key=lambda p: int(p[0]),
        reverse=True,
    )
    if other_years:
        html.append(f"<h2>Other {make} {model} Model Years</h2>")
        html.append("<ul>")
        for y, file_name in other_years:
            html.append(f'<li><a href="{file_name}">{y} {make} {model} Tire Pressure Guide</a></li>')
        html.append("</ul>")

    other_models = []
    for (mk, md), lst in pages_by_model.items():
        if mk == make and md != model:
            latest = max(lst, key=lambda p: int(p[0]))
            other_models.append((md, latest))
    other_models.sort(key=lambda x: x[0])
    if other_models:
        offset = seed % len(other_models)
        other_models = other_models[offset:] + other_models[:offset]
        html.append(f"<h2>More {make} Tire Pressure Guides</h2>")
        html.append("<ul>")
        for md, (y, file_name) in other_models[:6]:
            html.append(f'<li><a href="{file_name}">{y} {make} {md} Tire Pressure Guide</a></li>')
        html.append("</ul>")

    html.append("</section>")
    return "\n".join(html)


# ============================================================
#  ГЕНЕРАЦІЯ СТОРІНОК МОДЕЛЕЙ
# ============================================================

# Словник для збереження посилань, згрупованих по брендах
generated_pages_by_make = defaultdict(list)
all_page_urls = []

# Генеруємо сторінку для кожної моделі
for (make, model, year), rows in models_data.items():
    rows_html = ""
    for r in rows:
        rows_html += f"""
            <tr>
                <td><strong>{r['trim']}</strong></td>
                <td>{r['tire_size']}</td>
                <td><strong>{r['front_psi']} PSI</strong></td>
                <td><strong>{r['rear_psi']} PSI</strong></td>
            </tr>
        """

    # Унікальний контент для сторінки (розрахунки, поради, FAQ, посилання)
    extra_html = build_extra_content(make, model, year, rows)
    meta_description = build_meta_description(make, model, year, rows)

    # Заповнюємо шаблон даними моделі
    page_content = template_content
    page_content = page_content.replace("{{make}}", make)
    page_content = page_content.replace("{{model}}", model)
    page_content = page_content.replace("{{year}}", year)
    page_content = page_content.replace("{{variants_rows}}", rows_html)
    page_content = page_content.replace("{{meta_description}}", meta_description)

    # Вставляємо додатковий контент:
    # 1) якщо в шаблоні є {{extra_content}} - вставляємо туди
    # 2) інакше - одразу після останньої таблиці
    # 3) інакше - перед </body>
    if "{{extra_content}}" in page_content:
        page_content = page_content.replace("{{extra_content}}", extra_html)
    elif "</table>" in page_content:
        pos = page_content.rfind("</table>") + len("</table>")
        page_content = page_content[:pos] + "\n" + extra_html + "\n" + page_content[pos:]
    elif "</body>" in page_content:
        pos = page_content.rfind("</body>")
        page_content = page_content[:pos] + extra_html + "\n" + page_content[pos:]
    else:
        page_content += extra_html

    # Формуємо назву файлу
    file_name = make_file_name(year, make, model)
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as out_file:
        out_file.write(page_content)

    # Додаємо URL у загальний список для sitemap
    all_page_urls.append(file_name)

    # Додаємо у загальний список по брендах для головної сторінки
    generated_pages_by_make[make].append({
        "title": f"{year} {model} Tire Pressure Guide",
        "url": file_name
    })

# Генеруємо сучасну та структуровану головну сторінку index.html
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Car Tire Pressure (PSI) & Size Directory</title>
    <meta name="description" content="Find factory recommended cold tire pressure (PSI) and OEM tire sizes for popular American cars, trucks, and SUVs by make and model.">
    <link rel="icon" type="image/png" href="favicon.png">
    <style>
        :root {
            --primary: #1d4ed8;
            --dark: #0f172a;
            --light: #f8fafc;
            --border: #cbd5e1;
            --text: #1e293b;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: var(--text);
            background-color: var(--light);
            line-height: 1.7;
            margin: 0;
            padding: 0;
        }
        header {
            background: var(--dark);
            color: white;
            padding: 2.5rem 1rem;
            text-align: center;
            border-bottom: 4px solid var(--primary);
        }
        header h1 {
            margin: 0 0 0.5rem 0;
            font-size: 2.2rem;
        }
        header p {
            margin: 0;
            color: #94a3b8;
            font-size: 1.1rem;
        }
        .container {
            max-width: 950px;
            margin: 2rem auto;
            background: white;
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        .brand-section {
            margin-bottom: 2.5rem;
        }
        .brand-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--dark);
            border-bottom: 2px solid var(--primary);
            padding-bottom: 0.4rem;
            margin-bottom: 1rem;
        }
        .models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }
        .model-card {
            background: #f8fafc;
            border: 1px solid var(--border);
            padding: 1.2rem;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        .model-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.1);
            transform: translateY(-2px);
        }
        .model-card a {
            color: var(--primary);
            text-decoration: none;
            font-weight: 600;
            font-size: 1.05rem;
            display: block;
        }
        .model-card a:hover {
            text-decoration: underline;
        }
        .disclaimer {
            background: #fffbeb;
            border: 1px solid #fef3c7;
            padding: 1.2rem;
            border-radius: 8px;
            font-size: 0.85rem;
            color: #92400e;
            margin-top: 3rem;
        }
        footer {
            text-align: center;
            padding: 2rem;
            font-size: 0.85rem;
            color: #64748b;
            border-top: 1px solid var(--border);
            margin-top: 3rem;
        }
        footer a {
            color: var(--primary);
            text-decoration: none;
        }
        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

    <header>
        <h1>US Vehicle Tire Pressure & Size Directory</h1>
        <p>Select your vehicle manufacturer and model to find factory-recommended cold PSI.</p>
    </header>

    <div class="container">
        <p>Proper tire inflation is vital for vehicle safety, fuel efficiency, and tire longevity. Browse our comprehensive directory of American cars, trucks, and SUVs below to find exact manufacturer specifications for every trim level and wheel size.</p>
"""

# Динамічно виводимо секції по брендах
for make in sorted(generated_pages_by_make.keys()):
    index_html += f"""
        <div class="brand-section">
            <div class="brand-title">{make}</div>
            <div class="models-grid">
    """
    for page in generated_pages_by_make[make]:
        index_html += f"""
                <div class="model-card">
                    <a href="{page['url']}">{page['title']} &rarr;</a>
                </div>
        """
    index_html += """
            </div>
        </div>
    """

index_html += f"""
        <!-- Legal Disclaimer -->
        <div class="disclaimer">
            <strong>Legal Disclaimer:</strong> The tire pressure guides provided on this website are for informational purposes only. Always verify recommended PSI levels using the official placard located on your vehicle's driver-side door jamb.
        </div>
    </div>

    <footer>
        <p>
            <a href="index.html">Home</a> | 
            <a href="about.html">About Us</a> | 
            <a href="contact.html">Contact Us</a> | 
            <a href="privacy.html">Privacy Policy</a>
        </p>
        <p>&copy; 2026 DataSpecsHub. All rights reserved.</p>
    </footer>

</body>
</html>
"""

with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as index_file:
    index_file.write(index_html)

# --- ГЕНЕРАЦІЯ SITEMAP.XML ---
base_url = "https://tires.dataspecshub.com"

sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

# Додаємо головну сторінку та E-E-A-T
static_pages = ["", "about.html", "contact.html", "privacy.html"]
for page in static_pages:
    url = f"{base_url}/{page}".rstrip("/")
    priority = "1.0" if page == "" else "0.3"
    sitemap_content += f'  <url>\n    <loc>{url}</loc>\n    <priority>{priority}</priority>\n  </url>\n'

# Додаємо всі згенеровані сторінки автомобілів
for page_url in all_page_urls:
    sitemap_content += f'  <url>\n    <loc>{base_url}/{page_url}</loc>\n    <priority>0.8</priority>\n  </url>\n'

sitemap_content += '</urlset>'

with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as sitemap_file:
    sitemap_file.write(sitemap_content)

# --- ГЕНЕРАЦІЯ ROBOTS.TXT ---
robots_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""

with open(os.path.join(output_dir, "robots.txt"), "w", encoding="utf-8") as robots_file:
    robots_file.write(robots_content)

total_models = sum(len(v) for v in generated_pages_by_make.values())
print(f"Успішно згенеровано сайт: {total_models} моделей + index.html + sitemap.xml + robots.txt у папці '{output_dir}'!")