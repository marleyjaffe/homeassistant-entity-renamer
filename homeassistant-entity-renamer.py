#!/usr/bin/env python3

import argparse
import config
import csv
import json
import re
import requests
import tabulate
import asyncio
import websockets

tabulate.PRESERVE_WHITESPACE = True

# Determine the protocol based on TLS configuration
TLS_S = "s" if config.TLS else ""

# Header containing the access token
headers = {
    "Authorization": f"Bearer {config.ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


def align_strings(table):
    alignment_char = "."

    if len(table) == 0:
        return table

    for column in range(len(table[0])):
        # Get the column data from the table
        column_data = [row[column] for row in table]

        # Find the maximum length of the first part of the split strings
        strings_to_align = [s for s in column_data if alignment_char in s]
        if len(strings_to_align) == 0:
            continue

        max_length = max([len(s.split(alignment_char)[0]) for s in strings_to_align])

        def align_string(s):
            s_split = s.split(alignment_char, maxsplit=1)
            if len(s_split) == 1:
                return s
            else:
                return f"{s_split[0]:>{max_length}}.{s_split[1]}"

        # Create the modified table by replacing the column with aligned strings
        table = [
            tuple(
                align_string(value) if i == column else value
                for i, value in enumerate(row)
            )
            for row in table
        ]

    return table


def list_entities(regex=None):
    # API endpoint for retrieving all entities
    api_endpoint = f"http{TLS_S}://{config.HOST}/api/states"

    # Send GET request to the API endpoint
    response = requests.get(api_endpoint, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = json.loads(response.text)

        # Extract entity IDs and friendly names
        entity_data = [
            (entity["attributes"].get("friendly_name", ""), entity["entity_id"])
            for entity in data
        ]

        # Filter the entity data if regex argument is provided
        if regex:
            filtered_entity_data = [
                (friendly_name, entity_id)
                for friendly_name, entity_id in entity_data
                if re.search(regex, entity_id)
            ]
            entity_data = filtered_entity_data

        # Sort the entity data by friendly name
        entity_data = sorted(entity_data, key=lambda x: x[0])

        # Output the entity data
        return entity_data

    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []


def process_entities(
    entity_data,
    search_regex,
    replace_regex=None,
    output_file=None,
    input_filename=None,
    yes=False,
    friendly_name_search=None,
    friendly_name_replace=None,
):
    rename_data = []
    # Flag to indicate if we're doing the console (non-CSV) workflow
    is_csv_workflow = bool(input_filename)
    if input_filename:
        # Read data from the input file
        with open(input_filename, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                entity_id = row["Current Entity ID"]
                friendly_name = row.get(
                    "Friendly Name", ""
                )  # Check if 'Friendly Name' is present
                new_entity_id = row.get(
                    "New Entity ID", ""
                )  # Check if 'New Entity ID' is present
                # The CSV workflow remains untouched
                rename_data.append((friendly_name, entity_id, new_entity_id))

        if not rename_data:
            print("No data found in the input file.")
            return

    else:
        # Non-CSV/console workflow: store 4-tuple for header/rows (Friendly Name, Current Entity ID, New Entity ID, New Friendly Name)
        # The "New Friendly Name" column always shows the actual result of the regex (if provided), even if unchanged.
        if replace_regex:
            for friendly_name, entity_id in entity_data:
                new_entity_id = re.sub(search_regex, replace_regex, entity_id)
                if friendly_name_search is not None and friendly_name_replace is not None:
                    # Always perform the substitution (even if result is unchanged)
                    new_friendly_name = re.sub(friendly_name_search, friendly_name_replace, friendly_name)
                else:
                    new_friendly_name = friendly_name
                rename_data.append((friendly_name, entity_id, new_entity_id, new_friendly_name))
        else:
            for friendly_name, entity_id in entity_data:
                if friendly_name_search is not None and friendly_name_replace is not None:
                    new_friendly_name = re.sub(friendly_name_search, friendly_name_replace, friendly_name)
                else:
                    new_friendly_name = friendly_name
                rename_data.append((friendly_name, entity_id, "", new_friendly_name))

    # Print diagnostics if --friendly-name-search and --friendly-name-replace are supplied (console only)
    if not is_csv_workflow and friendly_name_search is not None and friendly_name_replace is not None:
        print(f"Applying friendly_name regex: re.sub({friendly_name_search!r}, {friendly_name_replace!r}, friendly_name)")
        # Show 1-2 sample mappings
        sample_count = 2 if len(rename_data) > 1 else 1
        samples = rename_data[:sample_count]
        print("Sample friendly name mappings (after applying regex):")
        for i, row in enumerate(samples):
            orig_name = row[0]
            new_name = row[3]
            print(f'  "{orig_name}" -> "{new_name}"' + (" [unchanged]" if orig_name == new_name else ""))
        print()  # Blank line before table

    # Print the table with new "New Friendly Name" column (console only)
    if not is_csv_workflow:
        # Prepare displayed table, setting "New Friendly Name" to "" unless both args are present
        if friendly_name_search is not None and friendly_name_replace is not None:
            display_rows = align_strings(rename_data)
        else:
            # Replace "New Friendly Name" column with empty string for all rows
            display_rows = [
                (row[0], row[1], row[2], "") for row in rename_data
            ]
        table = [
            ("Friendly Name", "Current Entity ID", "New Entity ID", "New Friendly Name")
        ] + display_rows
        print(tabulate.tabulate(table, headers="firstrow", tablefmt="github"))
    else:
        # Legacy table display (should almost never hit; CSV disables display)
        table = [("Friendly Name", "Current Entity ID", "New Entity ID")] + align_strings(
            rename_data
        )
        print(tabulate.tabulate(table, headers="firstrow", tablefmt="github"))

    # Write to CSV file if output file is provided (CSV format unchanged)
    table = [("Friendly Name", "Current Entity ID", "New Entity ID")] + [
        row[:3] for row in rename_data
    ]
    if output_file:
        write_to_csv(table, output_file)

    # Ask user for confirmation if replace_regex is provided or if reading from input file
    if not replace_regex and not input_filename:
        return

    if not yes:
        answer = input("\nDo you want to proceed with renaming the entities? (y/N): ")
        if answer.lower() not in ["y", "yes"]:
            print("Renaming process aborted.")
            return
    else:
        print("\nProceeding with renaming (confirmation skipped by --yes/-y).")

    asyncio.run(rename_entities(rename_data))


async def rename_entities(rename_data):

    ha_url = f"ws{TLS_S}://{config.HOST}/api/websocket"
    auth_msg = json.dumps({"type": "auth", "access_token": config.ACCESS_TOKEN})

    async with websockets.connect(ha_url) as websocket:

        auth_request = await websocket.recv()
        # print(f"<<< {auth_request}")

        await websocket.send(auth_msg)
        # print(f">>> {auth_msg}")

        auth_result = await websocket.recv()
        # print(f"<<< {auth_result}")

        # Rename the entities
        # For backward compatibility, support either 3- or 4-tuple
        for index, row in enumerate(rename_data, start=1):
            # Unpack 4-tuple or 3-tuple depending on workflow
            if len(row) == 4:
                original_friendly_name, entity_id, new_entity_id, new_friendly_name = row
                friendly_name_to_use = new_friendly_name
            else:
                original_friendly_name, entity_id, new_entity_id = row
                friendly_name_to_use = original_friendly_name
            entity_registry_update_msg = {
                "id": index,
                "type": "config/entity_registry/update",
                "entity_id": entity_id,
            }
            if new_entity_id:
                entity_registry_update_msg["new_entity_id"] = new_entity_id
            if friendly_name_to_use:
                entity_registry_update_msg["name"] = friendly_name_to_use

            await websocket.send(json.dumps(entity_registry_update_msg))
            # print(f">>> {entity_registry_update_msg}")

            ws_update_result = await websocket.recv()
            # print(f"<<< {ws_update_result}")

            update_result = json.loads(ws_update_result)
            if update_result.get("success"):
                success_msg = f"Entity '{entity_id}'"
                if new_entity_id:
                    success_msg += f" renamed to '{new_entity_id}'"
                if friendly_name_to_use:
                    success_msg += f" with friendly name '{friendly_name_to_use}'"
                success_msg += " successfully!"
                print(success_msg)
            else:
                print(
                    f"Failed to update entity '{entity_id}': {update_result.get('error', {}).get('message', 'Unknown error')}"
                )


def write_to_csv(table, filename):
    def _running_in_docker():
        try:
            # /.dockerenv is always present in normal Docker, /proc/1/cgroup may have 'docker' or 'kubepods'
            if open("/.dockerenv"):  # noqa: SIM115
                return True
        except Exception:
            pass
        try:
            with open("/proc/1/cgroup") as f:
                content = f.read()
                if "docker" in content or "kubepods" in content:
                    return True
        except Exception:
            pass
        return False

    # Only warn if run inside Docker and path is NOT under /data, /mnt, or /output
    if _running_in_docker() and not (
        str(filename).startswith("/data")
        or str(filename).startswith("/output")
        or str(filename).startswith("/mnt")
    ):
        print(
            f"WARNING: Output file '{filename}' does not reside under /data, /output, or /mnt. "
            "This file may not be accessible from your host unless you map a Docker volume to this location."
        )
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(table)
        print(f"(Table written to {filename})")


def main():
    parser = argparse.ArgumentParser(description="HomeAssistant Entity Renamer")
    parser.add_argument(
        "--input-file",
        dest="input_file",
        help="Input CSV file containing Friendly Name, Current Entity ID, and New Entity ID. "
             "If specified, all search/replace options are ignored and CSV workflow is used.",
    )
    parser.add_argument(
        "--search",
        dest="search_regex",
        help="Regular expression for searching entity IDs (ignored if --input-file is used).",
    )
    parser.add_argument(
        "--replace",
        dest="replace_regex",
        help="Replacement string for entity ID search. Requires --search (ignored with --input-file)."
    )
    parser.add_argument(
        "--friendly-name-search",
        dest="friendly_name_search",
        help="[Optional] Regular expression to search over friendly names. "
             "If set (and --input-file is NOT used), each friendly name will be transformed using re.sub. "
             "Requires --friendly-name-replace."
    )
    parser.add_argument(
        "--friendly-name-replace",
        dest="friendly_name_replace",
        help="[Optional] Replacement string for friendly name search. "
             "Requires --friendly-name-search. Ignored with --input-file."
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        help="Output CSV file to export the results",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt and proceed non-interactively."
    )
    args = parser.parse_args()

    # Validate argument combinations
    if args.input_file:
        if args.search_regex or args.replace_regex or args.friendly_name_search or args.friendly_name_replace:
            print(
                "Error: --input-file cannot be combined with "
                "--search/--replace/--friendly-name-search/--friendly-name-replace."
            )
            return
    if args.replace_regex and not args.search_regex:
        print("Error: --replace requires --search.")
        return
    if args.friendly_name_search and not args.friendly_name_replace:
        print("Error: --friendly-name-search requires --friendly-name-replace.")
        return
    if args.friendly_name_replace and not args.friendly_name_search:
        print("Error: --friendly-name-replace requires --friendly-name-search.")
        return

    if args.search_regex:
        if entity_data := list_entities(args.search_regex):
            process_entities(
                entity_data,
                args.search_regex,
                args.replace_regex,
                args.output_file,
                None,
                args.yes,
                args.friendly_name_search,
                args.friendly_name_replace,
            )
        else:
            print("No entities found matching the search regex.")
    elif args.input_file:
        input_file = args.input_file
        output_file = args.output_file

        process_entities([], None, None, output_file, input_file, args.yes)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
