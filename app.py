from flask import Flask, render_template, request
import pypokedex
import random
import requests

app = Flask(__name__)

REGION_DEX_RANGES = {
    "kanto": (1, 151),
    "johto": (152, 251),
    "hoenn": (252, 386),
    "sinnoh": (387, 493),
    "unova": (494, 649),
    "kalos": (650, 721),
    "alola": (722, 809),
    "galar": (810, 898),
    "paldea": (899, 1025),
    "blueberry": [84,85,102,103,111,112,464,48,49,239,125,466,240,126,467,440,113,242,123,212,900,128,522,523,203,981,551,552,553,953,954,627,628,629,630,667,668,585,586,235,479,479,479,479,479,479,868,869,328,329,330,731,732,733,72,73,116,117,230,779,546,547,764,287,288,289,43,44,45,182,50,51,88,89,335,336,739,740,741,741,741,741,79,80,199,170,171,686,687,370,456,457,594,324,661,662,663,751,752,236,106,107,237,74,75,76,529,530,574,575,576,677,678,774,408,409,410,411,572,573,227,333,334,81,82,462,311,312,559,560,622,623,322,323,854,855,137,233,474,595,596,602,603,604,374,375,376,610,611,612,86,87,131,211,904,577,578,579,209,210,613,614,27,28,37,38,459,460,884,1018,1019,1,2,3,4,5,6,7,8,9,152,153,154,155,156,157,158,159,160,252,253,254,255,256,257,258,259,260,387,388,389,390,391,392,393,394,395,495,496,497,498,499,500,501,502,503,650,651,652,653,654,655,656,657,658,722,723,724,725,726,727,728,729,730,810,811,812,813,814,815,816,817,818,1020,1021,1023,1022,1024,1009,1010,1025],
    "all": (1, 1025)
}

def is_fully_evolved(pokemon_name):
    try:
        species_data = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}").json()
        evo_chain_url = species_data["evolution_chain"]["url"]
        chain = requests.get(evo_chain_url).json()["chain"]

        def find_final(chain):
            if not chain["evolves_to"]:
                return [chain["species"]["name"]]
            final = []
            for evo in chain["evolves_to"]:
                final += find_final(evo)
            return final

        return pokemon_name in find_final(chain)
    except:
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    showdown_export = ""
    if request.method == "POST":
        poke_type = request.form.get("type").lower()
        region = request.form.get("region").lower()
        fully_evolved = request.form.get("evolved") == "yes"
        min_bst = int(request.form.get("min_bst") or 0)
        max_bst = int(request.form.get("max_bst") or 2000)
        num_random = int(request.form.get("num_random") or 6)
        random_moves = request.form.get("random_moves") == "on"
        
        dex_range = REGION_DEX_RANGES.get(region, (1, 1025))
        if isinstance(dex_range, tuple):
            dex_list = range(dex_range[0], dex_range[1] + 1)
        else:
            dex_list = dex_range
        matching = []

        tera_types = [
            "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", 
            "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", 
            "steel", "fairy"
        ]

        for dex in dex_list:
            try:
                pokemon = pypokedex.get(dex=dex)
                if poke_type != "all" and poke_type not in pokemon.types:
                    continue
                if fully_evolved and not is_fully_evolved(pokemon.name):
                    continue
                bst = sum([
                    pokemon.base_stats.hp,
                    pokemon.base_stats.attack,
                    pokemon.base_stats.defense,
                    pokemon.base_stats.sp_atk,
                    pokemon.base_stats.sp_def,
                    pokemon.base_stats.speed
                ])
                if not (min_bst <= bst <= max_bst):
                    continue

                abilities = [ability.name for ability in pokemon.abilities]
                random_ability = random.choice(abilities)
                
                random_tera_type = random.choice(tera_types)

                moves = []
                if random_moves:
                    scarlet_violet_moves = [move.name for move in pokemon.moves.get("scarlet-violet", [])]
                    if scarlet_violet_moves:
                        moves = random.sample(scarlet_violet_moves, min(4, len(scarlet_violet_moves)))

                stats = {
                    "hp": pokemon.base_stats.hp,
                    "attack": pokemon.base_stats.attack,
                    "defense": pokemon.base_stats.defense,
                    "sp_atk": pokemon.base_stats.sp_atk,
                    "sp_def": pokemon.base_stats.sp_def,
                    "speed": pokemon.base_stats.speed
                }

                matching.append({
                    "name": pokemon.name.capitalize(),
                    "dex": pokemon.dex,
                    "types": ", ".join(pokemon.types),
                    "sprite": pokemon.sprites.front.get("default", ""),
                    "moves": moves,
                    "stats": stats,
                    "ability": random_ability,
                    "tera_type": random_tera_type
                })
            except Exception as e:
                continue

        results = random.sample(matching, min(num_random, len(matching)))

        showdown_export = ""
        for poke in results:
            moves = poke["moves"]
            move_str = "\n- ".join(moves) if moves else ""
            
            showdown_export += f"{poke['name']}\n"
            showdown_export += f"Ability: {poke['ability'].capitalize()}\n"
            showdown_export += f"Tera Type: {poke['tera_type'].capitalize()}\n"
            showdown_export += f"- {move_str}\n\n"
            
    return render_template("index.html", results=results, showdown_export=showdown_export)

import webbrowser
webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    app.run(debug=True)