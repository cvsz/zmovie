#!/usr/bin/env python3
"""zMovie cinematic prompt generator.

Generates production-ready 20-second continuous long-take action prompts for
Wan 3.0-style text-to-video workflows. Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from typing import Sequence


SETTINGS = [
    "a lavish luxury hotel ballroom with floor-to-ceiling windows overlooking a neon city skyline",
    "a neon-lit casino hall with mirrored columns, velvet gaming tables, and polished stone floors",
    "a penthouse reception lounge with panoramic windows, designer furniture, and glossy marble surfaces",
    "a grand opera hall with gilded balconies, crystal chandeliers, and red velvet seating",
    "the interior of a luxury yacht with glass walls, lacquered wood, and moonlit ocean reflections",
    "a private art gallery with monumental sculptures, polished concrete, and dramatic museum lighting",
    "an embassy banquet hall with gold-trimmed architecture, long dining tables, and towering windows",
    "a rooftop sky bar enclosed by glass with luminous city towers surrounding it",
    "a high-end train dining carriage with brass details, linen-covered tables, and rain streaking the windows",
    "a marble palace corridor lined with chandeliers, statues, and tall arched windows",
]

TIMES = [
    "at night",
    "late in the evening",
    "just before dawn while the city lights are still glowing",
]

FACES = [
    "sharp green eyes, bold dark brows, deep red lips, and refined features",
    "cool grey eyes, defined brows, soft blush makeup, and an elegant composed expression",
    "striking amber eyes, glossy lips, delicate features, and a focused gaze",
    "icy blue eyes, porcelain-toned skin, subtle eyeliner, and an unreadable expression",
]

HAIR = [
    "long dark hair tied in a ribboned ponytail",
    "shoulder-length silky black hair",
    "soft wavy brown hair",
    "sleek straight hair with loose strands framing her face",
    "an elegant braided hairstyle with a few natural flyaway strands",
]

OUTFITS = [
    "a fitted pastel-pink cardigan, white pleated mini skirt, delicate ribbon collar, white ankle socks, and elegant Mary Jane shoes",
    "a cream cardigan, plaid pleated skirt, lace-collar blouse, white socks, and glossy loafers",
    "a soft-blue knit top, short pleated skirt, bow-tie blouse, ankle socks, and classic low pumps",
    "a pastel-lavender cardigan, white pleated skirt, ribbon necktie, ankle socks, and low heels",
    "a pale-mint fitted cardigan, ivory pleated skirt, small satin bow, white ankle socks, and polished Mary Jane shoes",
]

PERSONALITIES = [
    "calm, graceful, and completely composed",
    "sweet-looking but emotionally unreadable",
    "elegant, refined, and quietly intimidating",
    "gentle in appearance but precise and lethal in action",
]

ATTACKERS = [
    "a large muscular assassin in dark tactical gear",
    "a scarred bodyguard in black combat clothing",
    "a masked hitman in fitted tactical armor",
    "a brutal enforcer wearing dark street-combat gear",
]

ATTACKER_STYLES = [
    "aggressive boxing-based power strikes",
    "heavy brawling punches, clinches, and grapples",
    "military close-quarters pressure and forceful takedown attempts",
    "violent rushdown pressure built around hooks, body shots, and grabs",
]

LEAD_STYLES = [
    "precise counter-based martial arts with evasive footwork",
    "elegant but devastating judo mixed with compact striking",
    "fast close-quarters combat built around parries, elbows, knees, and throws",
    "highly technical kickboxing blended with grappling reversals",
    "fluid redirection, sharp counters, and momentum-based throws",
]

DESTRUCTION = [
    "a decorative glass partition exploding around them",
    "a polished marble table cracking under a body impact",
    "a row of chairs collapsing as both fighters crash through it",
    "a wooden banquet table splintering while glassware scatters across the floor",
    "a mirrored wall panel shattering into glittering fragments",
]

ENDINGS = [
    "she calmly fixes her cardigan, straightens her skirt, adjusts her ribbon, and walks away",
    "she adjusts her ribbon, gives the defeated attacker a cold glance, and exits without another reaction",
    "she smooths her skirt, restores her posture, and leaves the ruined room with measured steps",
    "she regains her breath, tucks a loose strand of hair behind her ear, and walks away as if nothing happened",
]

CAMERAS = [
    "dynamic handheld tracking with tight circular movement and aggressive but controlled whip pans",
    "fluid gimbal-like tracking punctuated by rapid crash-ins on major impacts",
    "intimate kinetic action cinematography with low-angle tracking and close orbiting movement",
    "premium Hollywood-style long-take camera motion with rapid reframing and seamless pursuit",
]

LIGHTING = [
    "warm chandelier light mixed with cool blue city light",
    "golden interior lighting contrasted with saturated neon reflections",
    "elegant ambient light with sharp highlights sparkling across broken glass",
    "soft luxury practical lighting mixed with moody night tones and glossy reflections",
]

VISUAL_STYLES = [
    "photorealistic, ultra-detailed 4K cinematic action film",
    "premium Hollywood action realism with high micro-detail and natural skin texture",
    "glossy high-contrast luxury action cinematography with realistic practical lighting",
    "photoreal cinematic realism with shallow depth of field, natural motion blur, and premium lens rendering",
]

FINISHERS = [
    "a perfectly timed judo-style shoulder throw",
    "a fast hip throw using the attacker's forward momentum",
    "an arm trap into a sweeping momentum-based takedown",
    "a pivoting sacrifice-style throw that redirects the final charge",
]

NEGATIVE_PROMPT = (
    "bad anatomy, extra limbs, missing limbs, broken hands, malformed fingers, face distortion, "
    "identity drift, inconsistent face, inconsistent hair, inconsistent costume, wardrobe color changes, "
    "random cuts, jump cuts, accidental scene transitions, temporal discontinuity, teleporting characters, "
    "jittery motion, strobing, frame warping, duplicated people, floating props, floaty physics, weightless impacts, "
    "weak contact, unrealistic body mechanics, impossible joint motion, poor choreography, sliding feet, "
    "broken environment continuity, debris resetting between frames, unnatural cloth simulation, frozen hair, "
    "blurry face, low detail, cartoon look, plastic skin, broken reflections, low-quality lighting, "
    "overexposed highlights, crushed shadows, underdetailed background"
)


@dataclass(frozen=True)
class Selection:
    setting: str
    time_of_day: str
    lead_face: str
    lead_hair: str
    lead_outfit: str
    lead_personality: str
    attacker: str
    attacker_style: str
    lead_fight_style: str
    destruction: str
    ending: str
    camera: str
    lighting: str
    visual_style: str
    finisher: str


def choose(rng: random.Random) -> Selection:
    return Selection(
        setting=rng.choice(SETTINGS),
        time_of_day=rng.choice(TIMES),
        lead_face=rng.choice(FACES),
        lead_hair=rng.choice(HAIR),
        lead_outfit=rng.choice(OUTFITS),
        lead_personality=rng.choice(PERSONALITIES),
        attacker=rng.choice(ATTACKERS),
        attacker_style=rng.choice(ATTACKER_STYLES),
        lead_fight_style=rng.choice(LEAD_STYLES),
        destruction=rng.choice(DESTRUCTION),
        ending=rng.choice(ENDINGS),
        camera=rng.choice(CAMERAS),
        lighting=rng.choice(LIGHTING),
        visual_style=rng.choice(VISUAL_STYLES),
        finisher=rng.choice(FINISHERS),
    )


def title_for(s: Selection) -> str:
    location_hint = s.setting.split(" with ", 1)[0].replace("a ", "", 1).replace("the interior of ", "")
    return f"Elegant Impact — {location_hint.title()}"


def build_prompt(s: Selection) -> str:
    return (
        f"A single continuous 20-second cinematic long take set inside {s.setting} {s.time_of_day}. "
        f"The environment is glamorous, expensive, and sophisticated, lit by {s.lighting}; polished surfaces, "
        "glass, furniture, and practical architectural details create readable spatial depth and believable opportunities for interaction. "
        "The entire video must remain one uninterrupted shot with no cuts, no hidden edits, and strict temporal, character, wardrobe, and damage continuity. "
        "[0:00–0:03] Medium tracking shot. A sophisticated woman with "
        f"{s.lead_face} and {s.lead_hair} walks calmly through the space. She wears {s.lead_outfit}. "
        f"Her demeanor is {s.lead_personality}. Without warning, {s.attacker} rushes toward her from behind using {s.attacker_style}. "
        "The camera recognizes the threat in the same continuous movement without abandoning her as the visual anchor. "
        "[0:03–0:06] She turns at the last instant, intercepts the first strike, then narrowly evades a rapid combination by ducking, pivoting, stepping off-line, and redirecting force with "
        f"{s.lead_fight_style}. The attacker tries to seize and throw her; she reverses the grip and drives him hard into nearby furniture. "
        "The camera orbits tightly while preserving readable geography, limb contact, eyelines, and impact direction. "
        "[0:06–0:09] He recovers and attacks low, knocking her balance away. She hits the floor with believable weight, rolls under a follow-up strike, plants a foot, rises immediately, and counters with a rapid sequence of compact punches, elbows, knee strikes, parries, and evasive steps. "
        "Her hair and clothing react naturally to acceleration and rotation; feet maintain believable traction and every strike shows anticipation, contact, recoil, and recovery. "
        "[0:09–0:12] The attacker catches her in a powerful clinch and drives her backward into "
        f"{s.destruction}. The camera follows directly through the impact in one fluid movement as fragments and furniture respond physically and remain displaced afterward. "
        "She lands, rolls across the floor, rises without a pause, and her expression becomes cold and focused as he charges again. "
        "[0:12–0:16] EXTREMELY INTENSE CONTINUOUS COMBAT PEAK. She parries a heavy punch, attacks the ribs, ducks under a hook, counters with a spinning kick, blocks a return strike, traps an arm, and uses the attacker's momentum to throw him across the room. "
        "He crashes into furniture, immediately regains his feet, and rushes back. She uses the environment, stepping onto a stable fallen object to gain leverage and launching into a powerful airborne counterstrike. "
        f"Camera behavior: {s.camera}. Each major collision receives a brief close crash-in before the camera flows onward; realistic motion blur, debris trajectories, cloth inertia, hair follow-through, body compression, and surface friction reinforce physical weight. "
        "[0:16–0:18] The attacker makes one final desperate committed attack. She catches and redirects the arm, pivots with precise timing, and finishes with "
        f"{s.finisher}, sending him decisively onto the floor. Loose fragments slide and settle across the reflective surface while the pre-existing environmental damage remains consistent. "
        "[0:18–0:20] Extreme close-up on her eyes as her breathing settles and one loose strand of hair falls naturally across her face. "
        f"{s.ending}. The camera eases away from her toward the damaged environment while the distant lights shimmer in reflection, ending on a controlled cinematic final image. "
        f"STYLE: {s.visual_style}, sophisticated feminine aesthetic contrasted with relentless high-intensity choreography, realistic martial-arts technique, physically accurate weight and momentum, natural skin texture, natural cloth and hair simulation, shallow depth of field, realistic motion blur, practical lighting, glossy reflections, detailed debris, coherent destruction, premium action cinematography, readable choreography, continuous camera motivation, high contrast, strong foreground-background separation, one shot, no cuts."
    )


def variations(rng: random.Random, current: Selection, count: int = 3) -> list[str]:
    items: list[str] = []
    for _ in range(count):
        alt = choose(rng)
        while alt.setting == current.setting and alt.lead_outfit == current.lead_outfit:
            alt = choose(rng)
        items.append(
            f"{alt.setting.capitalize()} {alt.time_of_day}; {alt.lead_outfit}; opponent: {alt.attacker}; finish with {alt.finisher}."
        )
    return items


def generate(rng: random.Random) -> dict[str, object]:
    selected = choose(rng)
    return {
        "title": title_for(selected),
        "main_prompt": build_prompt(selected),
        "negative_prompt": NEGATIVE_PROMPT,
        "parameter_breakdown": asdict(selected),
        "variation_ideas": variations(rng, selected),
    }


def render_text(item: dict[str, object], index: int | None = None) -> str:
    prefix = f"GENERATION {index}\n\n" if index is not None else ""
    params = item["parameter_breakdown"]
    assert isinstance(params, dict)
    ideas = item["variation_ideas"]
    assert isinstance(ideas, list)
    parameter_lines = "\n".join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in params.items())
    variation_lines = "\n".join(f"{i}. {value}" for i, value in enumerate(ideas, start=1))
    return (
        f"{prefix}TITLE\n{item['title']}\n\n"
        f"MAIN PROMPT\n{item['main_prompt']}\n\n"
        f"NEGATIVE PROMPT\n{item['negative_prompt']}\n\n"
        f"PARAMETER BREAKDOWN\n{parameter_lines}\n\n"
        f"OPTIONAL VARIATION IDEAS\n{variation_lines}"
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cinematic Wan 3.0 action prompts.")
    parser.add_argument("--count", type=int, default=1, help="number of prompts to generate (default: 1)")
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducible output")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of formatted text")
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be at least 1")
    if args.count > 1000:
        parser.error("--count must not exceed 1000")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    rng = random.Random(args.seed)
    results = [generate(rng) for _ in range(args.count)]

    if args.json:
        payload: object = results[0] if args.count == 1 else results
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    rendered = [render_text(item, i if args.count > 1 else None) for i, item in enumerate(results, start=1)]
    print("\n\n" + ("\n\n" + "=" * 88 + "\n\n").join(rendered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
