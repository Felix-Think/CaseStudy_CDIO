import argparse
from pathlib import Path

from casestudy.utils.background_image import (
    DEFAULT_OUTPUT_NAME,
    DEFAULT_SEED,
    generate_background_image,
    load_scene_payload,
)

CASES_DIR = Path(__file__).parent / "casestudy" / "cases"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sinh anh nen dua tren thong tin scene va luu vao thu muc case tuong ung."
    )
    parser.add_argument("case_id", help="case_id muon sinh anh va la noi luu file")
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Seed co dinh cho model (mac dinh: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--output-name",
        default=DEFAULT_OUTPUT_NAME,
        help="Ten file anh ket qua.",
    )
    parser.add_argument(
        "--prompt",
        help="Prompt tuy chon. Neu bo trong, script se doc scene tu context.json cua case.",
    )
    parser.add_argument(
        "--access-token",
        help="Access token override. Mac dinh lay GEMINI_ACCESS_TOKEN hoac token mau.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scene = index_event = None
    if args.prompt:
        print("Dang su dung prompt duoc truyen thu cong.")
    else:
        try:
            scene, index_event = load_scene_payload(CASES_DIR, args.case_id)
        except Exception as exc:
            raise RuntimeError(f"Khong tim thay scene cho case '{args.case_id}': {exc}") from exc
        print("Dang su dung prompt sinh tu scene trong context.json.")

    result = generate_background_image(
        case_id=args.case_id,
        base_dir=CASES_DIR,
        prompt=args.prompt,
        scene=scene,
        index_event=index_event,
        seed=args.seed,
        file_name=args.output_name,
        access_token=args.access_token,
    )
    print(f"Dang gui prompt toi Gemini cho case '{args.case_id}':\n{result.prompt}\n")
    print(f"Anh nen da duoc luu tai: {result.file_path}")


if __name__ == "__main__":
    main()
