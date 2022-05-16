import argparse
import re
import subprocess


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audio Output Switcher",
    )
    parser.add_argument(
        "-l",
        "--list-devices",
        help="list audio outputs",
        action='store_true'
    )
    parser.add_argument(
        "-d",
        "--device",
        help="switch to this specific output"
    )
    parser.add_argument(
        "-o",
        "--outputs",
        help="limit switcher to the listed outputs",
        action='append',
    )
    return parser.parse_args()


# noinspection SpellCheckingInspection
def _pacmd_to_dict() -> tuple[str, dict[str, int]]:
    starred_device: bool = False
    indexes: list[int] = []
    outputs: list[str] = []
    current_output: str = ''
    for line in subprocess.run(
            ['pacmd', 'list-sinks'],
            capture_output=True,
            text=True
    ).stdout.splitlines():
        if index_pattern_found := re.search("(.*?)index: (\d+)", line):
            indexes.append(int(index_pattern_found.group(2)))
            starred_device = True if "*" in index_pattern_found.group(1) else False
        elif device_pattern_found := re.search("\s+device.description = \"(.*?)\"", line):
            outputs.append(device_pattern_found.group(1))
            if starred_device:
                current_output = device_pattern_found.group(1)

    assert(len(indexes) == len(outputs))
    return current_output, {k: v for k, v in zip(outputs, indexes)}


def print_outputs(output_dict: dict[str, int]):
    for output in output_dict:
        print(output)


def set_output(index, output):
    subprocess.run(
        ['pacmd', 'set-default-sink', f'{output}'],
        capture_output=True,
        text=True
    )
    subprocess.run(
        ['notify-send', '-h', 'int:transient:1', '-i', 'audio-x-generic', f'Audio switched to {index}'],
        capture_output=True,
        text=True
    )


def assert_output_exists(output, output_dict):
    try:
        assert (output in output_dict)
    except AssertionError:
        print(f"{output} is not a valid choice. Please choose from the following:")
        print_outputs(output_dict.keys())
        raise AssertionError()


def main():
    args = _parse_args()
    current_output, output_dict = _pacmd_to_dict()

    match vars(args):
        case {'list_devices': True}:
            print_outputs(output_dict)
        case {'device': output} if output is not None:
            assert_output_exists(output, output_dict)
            set_output(output, output_dict[output])
        case {'outputs': outputs} if outputs is not None:
            for output in outputs:
                assert_output_exists(output, output_dict)
            output_dict = {k: output_dict[k] for k in outputs}

    output_iter = iter(output_dict.values())
    while key := next(output_iter):
        if key == current_output:
            set_output("Next Output", next(output_iter))
            break
    else:
        key = next(iter(output_dict))
        set_output(key, output_dict[key])


if __name__ == "__main__":
    main()
