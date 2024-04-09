from PIL import Image
import json
import ast

def get_raw_metadata(image: Image) -> dict:
    return (image.info or {}).copy()

def is_json(data: str) -> bool:
    try:
        loaded_json = json.loads(data)
        assert isinstance(loaded_json, dict)
    except (ValueError, AssertionError):
        return False
    return True

def get_parameters_and_scheme(raw_metadata) -> tuple[dict | str, str]:
    # Adaptation of https://github.com/lllyasviel/Fooocus/blob/main/modules/meta_parser.py#L565
    parameters = raw_metadata.pop('parameters', None)
    metadata_scheme = raw_metadata.pop('fooocus_scheme', None)
    exif = raw_metadata.pop('exif', None)
    if parameters is not None and is_json(parameters):
        parameters = json.loads(parameters)
    elif exif is not None:
        exif = raw_metadata.getexif()
        # 0x9286 = UserComment
        parameters = exif.get(0x9286, None)
        # 0x927C = MakerNote
        metadata_scheme = exif.get(0x927C, None)
        if is_json(parameters):
            parameters = json.loads(parameters)
    if not metadata_scheme in ["fooocus", "a1111"]:
        metadata_scheme = None
        # broad fallback
        if isinstance(parameters, dict):
            metadata_scheme = "fooocus"
        if isinstance(parameters, str):
            metadata_scheme = "a1111"
    return parameters, metadata_scheme

def parse_fooocus_parameters(parameters: dict) -> dict:
    positive = parameters["prompt"] or ""
    negative = parameters["negative_prompt"].split("unrealistic, saturated, high contrast, big nose, painting, drawing, sketch, cartoon, anime, manga, render, CG, 3d, watermark, signature, label")[0] or ""
    model = parameters["base_model"] or ""
    return {"positive": positive, "negative": negative, "model": model}

def parse_automatic_parameters(parameters: dict) -> dict:
    positive = parameters.split("\n")[0] or ""
    negative = parameters.split("\n")[1].replace("Negative prompt: ", "") or ""
    model = ""
    for parameter in parameters.split(", "):
        if parameter.startswith("Model: "):
            model = parameter.replace("Model: ", "")
    return {"positive": positive, "negative": negative, "model": model}

def extract_info(raw_metadata: str) -> dict:
    parameters, metadata_scheme = get_parameters_and_scheme(raw_metadata)
    if metadata_scheme == "fooocus":
        return parse_fooocus_parameters(parameters)
    elif metadata_scheme == "a1111":
        return parse_automatic_parameters(parameters)
    else:
        print("Failed to interpret metadata.")
        return {"positive": "", "negative": "", "model": ""}


def extract_metadata(image_path: str) -> tuple[str, str, str]:
    if image_path is None: # handles the case when image is removed
        return "", "", ""
    raw_metadata = get_raw_metadata(Image.open(image_path))
    info_dict = extract_info(raw_metadata)
    return info_dict["positive"], info_dict["negative"], info_dict["model"]
    